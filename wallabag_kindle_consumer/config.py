class Config:

    def __init__(self, db_uri, refresh_grace=120, consume_interval=30):
        self.db_uri = db_uri
        self.refresh_grace = refresh_grace
        self.consume_interval = consume_interval