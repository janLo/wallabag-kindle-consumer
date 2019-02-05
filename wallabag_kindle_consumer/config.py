import dataclasses
import configparser
import os

from logbook import Logger

logger = Logger(__name__)


@dataclasses.dataclass
class Config:
    wallabag_host: str
    db_uri: str
    client_id: str
    client_secret: str
    domain: str
    smtp_from: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_passwd: str
    tag: str = "kindle"
    refresh_grace: int = 120
    consume_interval: int = 30
    interface_host: str = "127.0.0.1"
    interface_port: int = 8080

    @staticmethod
    def from_file(filename):
        logger.info("read config from file {file}", file=filename)

        if not os.path.exists(filename):
            logger.warn("Config file {filename} does not exist", filename=filename)
            return None

        parser = configparser.ConfigParser()
        parser.read(filename)

        if 'DEFAULT' not in parser:
            logger.warn("Config file {filename} does not contain a section DEFAULT", filename=filename)
            return None

        dflt = parser['DEFAULT']

        tmp = {}
        missing = []
        for field in dataclasses.fields(Config):
            if field.name in dflt:
                tmp[field.name] = field.type(dflt[field.name])
            else:
                if field.default is dataclasses.MISSING:
                    missing.append(field.name)

        if 0 != len(missing):
            logger.warn("Config file {filename} does not contain configs for: {lst}", filename=filename,
                        lst=", ".join(missing))
            return None

        return Config(**tmp)

    @staticmethod
    def from_env():
        logger.info("Read config from environment")
        tmp = {}
        missing = []
        for field in dataclasses.fields(Config):
            if field.name.upper() in os.environ:
                tmp[field.name] = field.type(os.environ[field.name.upper()])
            else:
                if field.default is dataclasses.MISSING:
                    missing.append(field.name.upper())

        if 0 != len(missing):
            logger.warn("Environment config does not contain configs for: {lst}", lst=", ".join(missing))
            return None

        return Config(**tmp)
