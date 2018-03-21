#!/usr/bin/env python3
import asyncio

from logbook import Logger
from sqlalchemy.orm import joinedload

from models import User, Job

logger = Logger(__name__)


class Consumer:
    def __init__(self, wallabag, session, sender, interval=30):
        self.wallabag = wallabag
        self.session = session
        self.interval = interval
        self.sender = sender
        self.running = True

    async def fetch_jobs(self, user):
        logger.info("Fetch entries for user {}", user.name)
        async for entry in self.wallabag.fetch_entries(user):
            logger.info("Schedule job to send entry {}", entry.id)
            job = Job(article=entry.id, title=entry.title, format=entry.tag.format)
            user.jobs.append(job)
            await self.wallabag.remove_tag(user, entry)

    async def process_job(self, job):
        logger.info("Process export for job {id} ({format})", id=job.article, format=job.format)
        data = await self.wallabag.export_article(job.user, job.article, job.format)
        await self.sender.send_mail(job, data)
        self.session.delete(job)

    async def consume(self):
        while self.running:
            logger.info("Start consume run")
            fetches = [self.fetch_jobs(user) for user in self.session.query(User).all()]
            await asyncio.gather(*fetches)
            self.session.commit()

            jobs = [self.process_job(job) for job in self.session.query(Job).options(joinedload('user'))]
            await asyncio.gather(*jobs)
            self.session.commit()

            asyncio.sleep(self.interval)

