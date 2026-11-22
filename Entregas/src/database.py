import os
from sqlalchemy.engine import URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

url = URL(
    drivername="postgresql",
    username="admin",
    password="adminE",
    host="dbhost",
    port="5432",
    database="Entregas",
)

engine = create_engine(url)
Session = sessionmaker(bind=engine)
session = Session()