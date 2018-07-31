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
    email = Column(String(320), unique=True, nullable=False)
    name = Column(String(80), nullable=False)
    building = Column(String(3), nullable=False)


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


engine = create_engine('sqlite:///drivewipe.db')

Base.metadata.create_all(engine)

engine = create_engine('sqlite:///drivewipe.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

myFirstUser = User(
    name="Chris Martin",
    email="cmart@oath.com",
    building="bf2")
session.add(myFirstUser)
session.commit()

myFirstDrive = Drive(
    serialno="S2Z5NY0HC12345",
    model="SM0256G",
    manf="Apple",
    wipe_status="Dirty",
    wipe_start=datetime.now(),
    wipe_end=datetime.now(),
    user_id="1")
session.add(myFirstDrive)
session.commit()

firstResult = session.query(User).first()
print("Database Setup completed, first user added:", firstResult.name)
