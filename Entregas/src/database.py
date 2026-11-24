import os
from sqlalchemy.engine import URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER", "admin"),
    password=os.getenv("DB_PASSWORD", "adminE"),
    host=os.getenv("DB_HOST", "db-entrega"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "Entrega"),
)

engine = create_engine(url)
Session = sessionmaker(bind=engine)
session = Session()