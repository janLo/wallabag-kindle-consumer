import asyncio
from datetime import datetime, timedelta

from logbook import Logger
from sqlalchemy import func

from wallabag_kindle_consumer.models import User

logger = Logger(__name__)


class Refresher:
    def __init__(self, session, wallabag):
        self.session = session
        self.wallabag = wallabag
        self.grace = 120

    def _wait_time(self):
        next = self.session.query(func.min(User.token_valid).label("min")).first()
        if next is None or next.min is None:
            return 3
        delta = next.min - datetime.utcnow()
        if delta < timedelta(seconds=self.grace):
            return 0

        calculated = delta - timedelta(seconds=self.grace)
        return calculated.total_seconds()

    async def refresh(self):
        while True:
            await asyncio.sleep(self._wait_time())

            ts = datetime.utcnow() + timedelta(seconds=self.grace)
            refreshes = [self._refresh_user(user) for user
                         in self.session.query(User).filter(User.token_valid < ts).all()]
            await asyncio.gather(*refreshes)

            self.session.commit()

    async def _refresh_user(self, user):
        logger.info("Refresh token for {}", user.name)
        await self.wallabag.refresh_token(user)
