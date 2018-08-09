from datetime import datetime
from sqlalchemy import create_engine
from database_setup import Base, User, Drive
from sqlalchemy.orm import relationship, sessionmaker

engine = create_engine('sqlite:///drivewipe.db')
DBSession = sessionmaker(bind=engine)
session = DBSession()

myFirstUser = User(
    name="Chris Martin",
    email="cmart22@gmail.com",
    building="bf2")
session.add(myFirstUser)
session.commit()

myFirstUser = User(
    name="Bob Bobson",
    email="bobooo@gmail.com.com",
    building="bf1")
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

myFirstDrive = Drive(
    serialno="S2Z5NY0HC54321",
    model="SM0256G",
    manf="Apple",
    wipe_status="Dirty",
    wipe_start=datetime.now(),
    wipe_end=datetime.now(),
    user_id="2")
session.add(myFirstDrive)
session.commit()