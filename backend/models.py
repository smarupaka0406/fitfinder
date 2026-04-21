from datetime import datetime
from sqlalchemy import Column, String, Float, Text, DateTime, Integer, Boolean, JSON, UniqueConstraint
from database import Base


class CatalogProduct(Base):
    __tablename__ = 'catalog_products'
    __table_args__ = (
        UniqueConstraint('retailer', 'source_product_id', name='uq_catalog_product_source'),
    )

    id = Column(String(100), primary_key=True)
    retailer = Column(String(50), nullable=False, index=True)
    source_product_id = Column(String(100), nullable=False)
    handle = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    normalized_title = Column(String(255), nullable=False, index=True)
    brand = Column(String(120), nullable=False)
    category = Column(String(120), nullable=False, index=True)
    price_min = Column(Float)
    price_max = Column(Float)
    compare_at_price_min = Column(Float)
    compare_at_price_max = Column(Float)
    hero_image_url = Column(Text)
    product_url = Column(Text, nullable=False)
    tags = Column(JSON)
    is_active = Column(Boolean, default=True)
    raw_payload = Column(JSON)
    image_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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
