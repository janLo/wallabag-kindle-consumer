from sqlalchemy import Integer, String, DateTime, Column, ForeignKey, Enum, Boolean
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    name = Column(String, primary_key=True)
    token = Column(String())
    auth_token = Column(String)
    refresh_token = Column(String)
    token_valid = Column(DateTime)
    last_check = Column(DateTime)
    email = Column(String)
    kindle_mail = Column(String)
    active = Column(Boolean, default=True)

    jobs = relationship('Job', backref='user')


class Job(Base):
    __tablename__ = "job"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article = Column(Integer)
    title = Column(String)
    user_name = Column(Integer, ForeignKey("user.name"))
    format = Column(Enum('pdf', 'mobi', 'epub'))


class ContextSession:
    def __init__(self, session_maker):
        self.session_maker = session_maker

    def __enter__(self):
        self.session = self.session_maker()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


def context_session(config):
    return ContextSession(session_maker(config))


def session_maker(config):
    Session = sessionmaker(autocommit=False,
                           autoflush=False,
                           bind=create_engine(config.db_uri))
    return Session


def create_db(config):
    engine = create_engine(config.db_uri)
    Base.metadata.create_all(engine)


def re_create_db(config):
    engine = create_engine(config.db_uri)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
