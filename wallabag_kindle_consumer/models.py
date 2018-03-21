from sqlalchemy import Integer, String, DateTime, Column, ForeignKey, Enum
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

    jobs = relationship('Job', backref='user')


class Job(Base):
    __tablename__ = "job"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article = Column(Integer)
    title = Column(String)
    user_name = Column(Integer, ForeignKey("user.name"))
    format = Column(Enum('pdf', 'mobi'))


def session_maker(uri):
    Session = sessionmaker(autocommit=False,
                           autoflush=False,
                           bind=create_engine(uri))
    return Session


def re_create_db(uri):
    engine = create_engine(uri)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
