import os

import aiohttp_jinja2
import jinja2
from aiohttp import web

from wallabag_kindle_consumer import wallabag


class ViewBase(web.View):
    @property
    def cfg(self):
        return self.request.app['config']

    def template(self, vars):
        vars.update({'wallabag_host': self.cfg.wallabag_host,
                     'tags': [t.tag for t in wallabag.make_tags(self.cfg.tag)]})
        return vars


class IndexView(ViewBase):
    @aiohttp_jinja2.template("index.html")
    async def get(self):
        return self.template({})

    @aiohttp_jinja2.template("index.html")
    async def post(self):
        data = await self.request.post()
        print(data)
        return self.template({})


@aiohttp_jinja2.template("relogin.html")
def re_login(request):
    pass


@aiohttp_jinja2.template("index.html")
def delete_user(request):
    pass


class App:
    def __init__(self, config):
        self.config = config
        self.app = web.Application()

        self.setup_app()
        self.setup_routes()

    def setup_app(self):
        self.app['config'] = self.config
        aiohttp_jinja2.setup(
            self.app, loader=jinja2.PackageLoader('wallabag_kindle_consumer', 'templates'))

        self.app['static_root_url'] = '/static'

    def setup_routes(self):
        self.app.router.add_static('/static/',
                                   path=os.path.join(os.path.dirname(__file__), 'static'),
                                   name='static')
        self.app.router.add_view("/", IndexView)

    def run(self):
        web.run_app(self.app, host=self.config.interface_host, port=self.config.interface_port)

    async def register_server(self, loop):
        await loop.create_server(self.app.make_handler(),
                                 self.config.interface_host, self.config.interface_port)
