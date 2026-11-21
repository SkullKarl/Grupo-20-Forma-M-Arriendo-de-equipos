from database.py import engine
from sqalchemy.orm import declarative_base
from sqalchemy import Column, Integer, String, Float

Base = declarative_base()

class ChargeRequests(Base):
    __table_name__ = "Charge Requests"
    Charge_Request_Id = Column(Integer, primary_key=True)
    Buy_Order = Column(String, nullable=False)
    Charge = Column(Float, nullable=False)

class RefundRequests(Base):
    __table_name__ = "Refund Requests"
    Refund_Request_Id = Column(Integer, primary_key=True)
    Charge = Column(Float, nullable=False)

Base.metadata.create_all(engine)