from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime

from sqlalchemy.sql import lambdas

Base = declarative_base()

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    image_path = Column(String)
    defects = Column(JSON)
    timestamp = Column(TIMESTAMP(timezone=True), default=lambda: datetime.utcnow())