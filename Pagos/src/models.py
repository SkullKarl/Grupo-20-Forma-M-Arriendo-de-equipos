from sqalchemy.orm import declarative_base
from sqalchemy import Column, Integer, String, Float

Base = declarative_base()

class ChargeRequests(Base):
    __table_name__ = "Charge Requests"
    ChargeRequest_id = Column(Integer, primary_key=True)
    session_id = Column(String, nullable=False)
    buy_order = Column(String, nullable=False)
    amount = Column(Float, nullable=False)

class RefundRequest(Base):
    __table_name__ = "refund_requests"
    RefundRequest_id = Column(Integer, primary_key=True)
    token = Column(String, nullable=False)
    amount = Column(Float, nullable=False)