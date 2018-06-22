from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from server.config import config

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(40), nullable=False)
    password = Column(String(40), nullable=False)

    def __call__(self):
        return {'id': self.id, 'username': self.username}


class Server(Base):
    __tablename__ = "servers"
    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)
    description = Column(Text)
    address = Column(Text, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    cycle = Column(Integer, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(Integer, nullable=False)
    state = Column(Integer, nullable=False)

    def __call__(self):
        return {i: self.__dict__.get(i) for i in filter(lambda x: x[0] != '_', list(self.__dict__))}


class Application(Base):
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)
    description = Column(Text)
    project_path = Column(Text, nullable=False)
    address = Column(Text, nullable=False)
    server_id = Column(Integer, ForeignKey('servers.id'), nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    cycle = Column(Integer, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(Integer, nullable=False)
    state = Column(Integer, nullable=False)

    def __call__(self):
        return {i: self.__dict__.get(i) for i in filter(lambda x: x[0] != '_', list(self.__dict__))}


def setupDB():
    """Init DB, insert fixed data"""
    db = create_engine('sqlite:///' + config['DATABASE'])
    Base.metadata.create_all(db)
    session = Session(db)
    session.add(User(username='root', password='root'))
    session.commit()
    session.close()


def getSession():
    db = create_engine('sqlite:///' + config['DATABASE'])
    return Session(db)
