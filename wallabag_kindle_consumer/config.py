class Config:

    def __init__(self, wallabag_host, db_uri, tag='kindle', refresh_grace=120, consume_interval=30,
                 interface_host="127.0.0.1", interface_port=8080):
        self.wallabag_host = wallabag_host
        self.db_uri = db_uri
        self.tag = tag
        self.refresh_grace = refresh_grace
        self.consume_interval = consume_interval
        self.interface_host = interface_host
        self.interface_port = interface_port
