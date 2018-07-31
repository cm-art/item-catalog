import os
import sys

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String(320), unique=True, nullable=False)
    first_name = Column(String(40), nullable=False)
    last_name = Column(String(40), nullable=False)
    building = Column(String(3), nullable=False)


class Assets(Base):
    __tablename__ = 'asset'

    tag = Column(String(20), primary_key=True)
    status = Column(String(20), nullable=False)
    hostname = Column(String(20), nullable=False)


class Drive(Base):
    __tablename__ = 'drive'

    serialno = Column(String(40), primary_key=True)
    manf = Column(String(40), nullable=False)
    model = Column(String(40), nullable=False)
    wipe_status = Column(DateTime, nullable=False)
    wipe_start = Column(DateTime, nullable=False)
    wipe_end = Column(String(10), nullable=False)
    asset_tag = Column(String(20), ForeignKey('asset.tag'))
    asset = relationship(Asset)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


engine = create_engine('sqlite:///drivewipe.db')

Base.metadata.create_all(engine)
