from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class Deliveries(Base):
    __tablename__ = "Deliveries"
    Delivery_Id = Column(Integer, primary_key=True, index=True)
    Equipment_Id = Column(String, nullable=False, index=True)
    Delivery_Date = Column(String, nullable=False)
    Status = Column(String, nullable=False, default="SCHEDULED")