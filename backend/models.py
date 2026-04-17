from datetime import datetime
from sqlalchemy import Column, String, Float, Text, DateTime
from database import Base

class SavedItem(Base):
    __tablename__ = 'saved_items'
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    original_price = Column(Float)
    image_url = Column(Text, nullable=False)
    product_link = Column(Text, nullable=False)
    similarity = Column(Float, nullable=False)
    category = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
