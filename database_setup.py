import os
import sys

from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String(320), nullable=False)
    name = Column(String(80), nullable=False)
    building = Column(String(3), nullable=False)
    picture = Column(String(250))


class Drive(Base):
    __tablename__ = 'drive'

    serialno = Column(String(40), primary_key=True)
    manf = Column(String(40), nullable=False)
    model = Column(String(40), nullable=False)
    wipe_status = Column(String(10), nullable=False)
    wipe_start = Column(DateTime)
    wipe_end = Column(DateTime)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


    @property
    def serialize(self):
        """Return data in serialized format for JSON printing"""
        return {
            'serialno': self.serialno,
            'manf': self.manf,
            'model': self.model,
            'wipe_status': self.wipe_status,
            'wipe_start': str(self.wipe_start),
            'wipe_end': str(self.wipe_end),
            'user_id': self.user_id,
        }


engine = create_engine('sqlite:///drivewipe.db')
Base.metadata.create_all(engine)

print("Database Setup completed")