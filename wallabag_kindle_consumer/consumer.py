#!/usr/bin/env python3
import asyncio

from logbook import Logger
from sqlalchemy.orm import joinedload

from wallabag_kindle_consumer.models import User, Job, context_session

logger = Logger(__name__)


class Consumer:
    def __init__(self, wallabag, cfg, sender):
        self.wallabag = wallabag
        self.sessionmaker = context_session(cfg)
        self.interval = cfg.consume_interval
        self.sender = sender
        self.running = True

    async def fetch_jobs(self, user):
        logger.debug("Fetch entries for user {}", user.name)
        async for entry in self.wallabag.fetch_entries(user):
            logger.info("Schedule job to send entry {}", entry.id)
            job = Job(article=entry.id, title=entry.title, format=entry.tag.format)
            user.jobs.append(job)
            await self.wallabag.remove_tag(user, entry)

    async def process_job(self, job, session):
        logger.info("Process export for job {id} ({format})", id=job.article, format=job.format)
        data = await self.wallabag.export_article(job.user, job.article, job.format)
        await self.sender.send_mail(job, data)
        session.delete(job)

    async def consume(self):
        while self.running:
            with self.sessionmaker as session:
                logger.debug("Start consume run")
                fetches = [self.fetch_jobs(user) for user in session.query(User).filter(User.active == True).all()]
                await asyncio.gather(*fetches)
                session.commit()

                jobs = [self.process_job(job, session) for job in session.query(Job).options(joinedload('user'))]
                await asyncio.gather(*jobs)
                session.commit()

            await asyncio.sleep(self.interval)

