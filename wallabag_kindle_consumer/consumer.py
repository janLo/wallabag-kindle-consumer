#!/usr/bin/env python3
import asyncio
import datetime

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

        self._wait_fut = None  # type: asyncio.Future

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

    async def _wait_since(self, since: datetime.datetime):
        now = datetime.datetime.utcnow()
        wait = max(0.0, self.interval - (now - since).total_seconds())

        if not self.running:
            return

        self._wait_fut = asyncio.ensure_future(asyncio.sleep(wait))

        try:
            await self._wait_fut
        except asyncio.CancelledError:
            pass
        finally:
            self._wait_fut = None

    async def consume(self):
        while self.running:
            start = datetime.datetime.utcnow()

            with self.sessionmaker as session:
                logger.debug("Start consume run")
                fetches = [self.fetch_jobs(user) for user in session.query(User).filter(User.active == True).all()]
                await asyncio.gather(*fetches)
                session.commit()

                jobs = [self.process_job(job, session) for job in session.query(Job).options(joinedload(Job.user))]
                await asyncio.gather(*jobs)
                session.commit()

            await self._wait_since(start)

    def stop(self):
        self.running = False
        self._wait_fut.cancel()
