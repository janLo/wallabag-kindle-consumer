#!/usr/bin/env python3

import argparse
import asyncio

import uvloop
import sys

from logbook import Logger, StreamHandler

from wallabag_kindle_consumer.config import Config
from wallabag_kindle_consumer.consumer import Consumer
from wallabag_kindle_consumer.interface import App
from wallabag_kindle_consumer.refresher import Refresher
from wallabag_kindle_consumer.sender import Sender
from wallabag_kindle_consumer.wallabag import Wallabag

StreamHandler(sys.stdout).push_application()
logger = Logger("kindle-consumer")


def parse_args():
    parser = argparse.ArgumentParser(description="Wallabag-Kindle-Consumer")
    parser.add_argument("--cfg", help="config file", required=False)
    parser.add_argument("--env", help="Read config from env", action="store_true")
    parser.add_argument("--refresher", help="Start token refresher", action="store_true")
    parser.add_argument("--interface", help="Start web interface", action="store_true")
    parser.add_argument("--consumer", help="Start article consumer", action="store_true")

    return parser.parse_args()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    loop = asyncio.get_event_loop()

    args = parse_args()

    config = Config.from_file("config.ini")

    if 'cfg' in args and args.cfg is not None:
        new = Config.from_file(args.cfg)
        if new is not None:
            config = new

    if 'env' in args and args.env:
        new = Config.from_env()
        if new is not None:
            config = new

    wallabag = Wallabag(config)
    sender = Sender(loop, config.smtp_from, config.smtp_host, config.smtp_port, config.smtp_user, config.smtp_passwd)

    if args.refresher:
        logger.info("Create Refresher")
        refresher = Refresher(config, wallabag, sender)
        loop.create_task(refresher.refresh())

    if args.consumer:
        logger.info("Create Consumer")
        consumer = Consumer(wallabag, config, sender)
        loop.create_task(consumer.consume())

    if args.interface:
        logger.info("Create Interface")
        webapp = App(config, wallabag)
        loop.create_task(webapp.register_server(loop))

    loop.run_forever()
