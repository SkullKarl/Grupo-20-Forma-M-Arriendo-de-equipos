from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Float, Integer, String

Base = declarative_base()

class ChargeRequests(Base):
    __tablename__ = "Charge Requests"
    Charge_Request_Id = Column(Integer, primary_key=True, index=True)
    Equipo_Id = Column(String, nullable=False)
    Buy_Order = Column(String, nullable=False)
    Charge = Column(Float, nullable=False)
    Idempotency_Key = Column(String, unique=True, index=True, nullable=False)
    Status = Column(String, nullable=False, default="PENDING")
    Token = Column(String, nullable=True)

class RefundRequests(Base):
    __tablename__ = "Refund Requests"
    Refund_Request_Id = Column(Integer, primary_key=True, index=True)
    Equipo_Id = Column(String, nullable=False)
    Charge = Column(Float, nullable=False)
    Status = Column(String, nullable=False, default="REFUNDED")
    Token = Column(String, nullable=False)