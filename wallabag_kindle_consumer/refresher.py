import asyncio
from datetime import datetime, timedelta

from logbook import Logger
from sqlalchemy import func

from .models import User, context_session

logger = Logger(__name__)


class Refresher:
    def __init__(self, config, wallabag):
        self.sessionmaker = context_session(config)
        self.wallabag = wallabag
        self.grace = config.refresh_grace

    def _wait_time(self, session):
        next = session.query(func.min(User.token_valid).label("min")).first()
        if next is None or next.min is None:
            return 3
        delta = next.min - datetime.utcnow()
        if delta < timedelta(seconds=self.grace):
            return 0

        calculated = delta - timedelta(seconds=self.grace)
        return calculated.total_seconds()

    async def refresh(self):
        while True:
            with self.sessionmaker as session:
                await asyncio.sleep(self._wait_time(session))

                ts = datetime.utcnow() + timedelta(seconds=self.grace)
                refreshes = [self._refresh_user(user) for user
                             in session.query(User).filter(User.token_valid < ts).all()]
                await asyncio.gather(*refreshes)

            session.commit()
            session.remove()

    async def _refresh_user(self, user):
        logger.info("Refresh token for {}", user.name)
        await self.wallabag.refresh_token(user)
