import os
import configparser

from logbook import Logger

logger = Logger(__name__)


class Config:
    known_values = ["wallabag_host", "db_uri", "client_id", "client_secret", "domain", "smtp_from", "smtp_host",
                    "smtp_port", "smtp_user", "smtp_passwd", "tag", "refresh_grace", "consume_interval",
                    "interface_host", "interface_port"]
    required_values = ["wallabag_host", "db_uri", "client_id", "client_secret", "domain", "smtp_from", "smtp_host",
                       "smtp_port", "smtp_user", "smtp_passwd"]

    def __init__(self, wallabag_host, db_uri, client_id, client_secret, domain, smtp_from, smtp_host, smtp_port,
                 smtp_user, smtp_passwd, tag='kindle', refresh_grace=120, consume_interval=30,
                 interface_host="127.0.0.1", interface_port=8080):
        self.wallabag_host = wallabag_host
        self.db_uri = db_uri
        self.client_id = client_id
        self.client_secret = client_secret
        self.domain = domain
        self.smtp_from = smtp_from
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_passwd = smtp_passwd
        self.tag = tag
        self.refresh_grace = refresh_grace
        self.consume_interval = consume_interval
        self.interface_host = interface_host
        self.interface_port = interface_port

    @staticmethod
    def from_file(filename):
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
        for key in Config.known_values:
            if key in dflt:
                tmp[key] = dflt[key]
            else:
                if key in Config.required_values:
                    missing.append(key)

        if 0 != len(missing):
            logger.warn("Config file {filename} does not contain configs for: {lst}", filename=filename,
                        lst=", ".join(missing))
            return None

        return Config(**tmp)

    @staticmethod
    def from_env():
        pass
