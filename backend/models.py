from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

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
    product_url = Column(Text, nullable=False)

    title = Column(String(255), nullable=False)
    normalized_title = Column(String(255), nullable=False, index=True)
    brand = Column(String(100), nullable=False)
    product_type = Column(String(100))
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100))
    gender = Column(String(50), index=True)

    color_primary = Column(String(100))
    color_raw = Column(String(255))
    material = Column(Text)
    description_html = Column(Text)
    description_text = Column(Text)
    tags = Column(JSON)

    price_min = Column(Float)
    price_max = Column(Float)
    compare_at_price_min = Column(Float)
    compare_at_price_max = Column(Float)
    currency = Column(String(10), default='USD')

    hero_image_url = Column(Text)
    image_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    published_at = Column(DateTime)
    source_created_at = Column(DateTime)
    source_updated_at = Column(DateTime)

    text_embedding = Column(JSON)
    image_embedding = Column(JSON)
    hero_image_phash = Column(String(32))
    canonical_group_id = Column(String(100))
    raw_payload = Column(JSON)

    ingested_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants = relationship(
        'CatalogProductVariant',
        back_populates='product',
        cascade='all, delete-orphan',
        order_by='CatalogProductVariant.position',
    )
    images = relationship(
        'CatalogProductImage',
        back_populates='product',
        cascade='all, delete-orphan',
        order_by='CatalogProductImage.position',
    )
    outgoing_matches = relationship(
        'CatalogProductMatch',
        foreign_keys='CatalogProductMatch.left_product_id',
        back_populates='left_product',
        cascade='all, delete-orphan',
    )
    incoming_matches = relationship(
        'CatalogProductMatch',
        foreign_keys='CatalogProductMatch.right_product_id',
        back_populates='right_product',
        cascade='all, delete-orphan',
    )


class CatalogProductVariant(Base):
    __tablename__ = 'catalog_product_variants'
    __table_args__ = (
        UniqueConstraint('product_id', 'source_variant_id', name='uq_catalog_variant_source'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(100), ForeignKey('catalog_products.id'), nullable=False, index=True)
    source_variant_id = Column(String(100), nullable=False)
    sku = Column(String(100))
    title = Column(String(100))
    size_value = Column(String(50), index=True)
    color_value = Column(String(100))
    price = Column(Float)
    compare_at_price = Column(Float)
    available = Column(Boolean, default=True)
    position = Column(Integer, default=0)
    raw_payload = Column(JSON)

    product = relationship('CatalogProduct', back_populates='variants')


class CatalogProductImage(Base):
    __tablename__ = 'catalog_product_images'
    __table_args__ = (
        UniqueConstraint('product_id', 'source_image_id', name='uq_catalog_image_source'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(100), ForeignKey('catalog_products.id'), nullable=False, index=True)
    source_image_id = Column(String(100), nullable=False)
    image_url = Column(Text, nullable=False)
    position = Column(Integer, default=0)
    width = Column(Integer)
    height = Column(Integer)
    phash = Column(String(32))
    image_embedding = Column(JSON)
    is_primary = Column(Boolean, default=False)
    raw_payload = Column(JSON)

    product = relationship('CatalogProduct', back_populates='images')


class CatalogProductMatch(Base):
    __tablename__ = 'catalog_product_matches'
    __table_args__ = (
        UniqueConstraint('left_product_id', 'right_product_id', name='uq_catalog_product_match_pair'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    left_product_id = Column(String(100), ForeignKey('catalog_products.id'), nullable=False, index=True)
    right_product_id = Column(String(100), ForeignKey('catalog_products.id'), nullable=False, index=True)
    image_score = Column(Float, nullable=False, default=0.0)
    text_score = Column(Float, nullable=False, default=0.0)
    price_score = Column(Float, nullable=False, default=0.0)
    attribute_score = Column(Float, nullable=False, default=0.0)
    final_score = Column(Float, nullable=False, default=0.0, index=True)
    match_status = Column(String(30), nullable=False, default='candidate', index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    left_product = relationship('CatalogProduct', foreign_keys=[left_product_id], back_populates='outgoing_matches')
    right_product = relationship('CatalogProduct', foreign_keys=[right_product_id], back_populates='incoming_matches')


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
