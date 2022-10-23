import aiohttp
from datetime import datetime, timedelta
from collections import namedtuple

from logbook import Logger

logger = Logger(__name__)


class Article:
    def __init__(self, id, tags, title, tag, **kwargs):
        self.id = id
        self.tags = tags
        self.title = title
        self.tag = tag

    def tag_id(self):
        for t in self.tags:
            if t['label'] == self.tag.tag:
                return t['id']

        return -1


Tag = namedtuple('Tag', ['tag', 'format'])


def make_tags(tag):
    return (Tag(tag='{tag}'.format(tag=tag), format='epub'),
            Tag(tag='{tag}-epub'.format(tag=tag), format='epub'),
            Tag(tag='{tag}-mobi'.format(tag=tag), format='mobi'),
            Tag(tag='{tag}-pdf'.format(tag=tag), format='pdf'))


class Wallabag:
    def __init__(self, config):
        self.config = config
        self.tag = "kindle"
        self.tags = make_tags(self.tag)

    async def get_token(self, user, passwd):
        params = {'grant_type': 'password',
                  'client_id': self.config.client_id,
                  'client_secret': self.config.client_secret,
                  'username': user.name,
                  'password': passwd}

        async with aiohttp.ClientSession() as session:
            async with session.get(self._url('/oauth/v2/token'), params=params) as resp:
                if resp.status != 200:
                    logger.warn("Cannot get token for user {user}", user=user.name)
                    return False
                data = await resp.json()
                user.auth_token = data["access_token"]
                user.refresh_token = data["refresh_token"]
                user.token_valid = datetime.utcnow() + timedelta(seconds=data["expires_in"])
                logger.info("Got new token for {}", user.name)

                return True

    async def refresh_token(self, user):
        params = {'grant_type': 'refresh_token',
                  'client_id': self.config.client_id,
                  'client_secret': self.config.client_secret,
                  'refresh_token': user.refresh_token,
                  'username': user.name}

        async with aiohttp.ClientSession() as session:
            async with session.get(self._url('/oauth/v2/token'), params=params) as resp:
                if resp.status != 200:
                    logger.warn("Cannot refresh token for user {user}", user=user.name)
                    return False
                data = await resp.json()
                user.auth_token = data["access_token"]
                user.refresh_token = data["refresh_token"]
                user.token_valid = datetime.utcnow() + timedelta(seconds=data["expires_in"])

                return True

    def _api_params(self, user, params=None):
        if params is None:
            params = {}

        params['access_token'] = user.auth_token
        return params

    def _url(self, url):
        return self.config.wallabag_host + url

    async def fetch_entries(self, user):
        if user.auth_token is None:
            logger.warn("No auth token for {}".format(user.name))
            return
        async with aiohttp.ClientSession() as session:
            for tag in self.tags:
                params = self._api_params(user, {"tags": tag.tag})
                async with session.get(self._url('/api/entries.json'), params=params) as resp:
                    if resp.status != 200:
                        logger.warn("Could not get entries of tag {tag} for user {user}", tag=tag.tag, user=user.name)
                        return

                    data = await resp.json()
                    if data['pages'] == 1:
                        user.last_check = datetime.utcnow()

                    articles = data['_embedded']['items']
                    for article in articles:
                        yield Article(tag=tag, **article)

    async def remove_tag(self, user, article):
        params = self._api_params(user)
        url = self._url('/api/entries/{entry}/tags/{tag}.json'.format(entry=article.id,
                                                                      tag=article.tag_id()))

        async with aiohttp.ClientSession() as session:
            async with session.delete(url, params=params) as resp:
                if resp.status != 200:
                    logger.warn("Cannot remove tag {tag} from entry {entry} of user {user}", user=user.name,
                                entry=article.id, tag=article.tag.tag)
                    return

                logger.info("Removed tag {tag} from article {article} of user {user}", user=user.name,
                            article=article.id, tag=article.tag.tag)

    async def export_article(self, user, article_id, format):
        params = self._api_params(user)
        url = self._url("/api/entries/{entry}/export.{format}".format(entry=article_id, format=format))

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warn("Cannot export article {article} of user {user} in format {format}", user=user.name,
                                article=article_id, format=format)
                    return

                return await resp.read()
