"""SQLAlchemy ORM models."""
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    reorder_threshold = Column(Integer, nullable=False, default=10)
    image_url = Column(String, default="")
    is_on_sale = Column(Boolean, default=False)
    sale_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    account_age_days = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")
    total_amount = Column(Float, nullable=False)
    tracking_number = Column(String, nullable=True)
    shipping_address = Column(String, default="")
    billing_address = Column(String, default="")
    payment_method = Column(String, default="Credit Card")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC),
                        onupdate=lambda: datetime.now(UTC))
    customer = relationship("Customer", backref="orders")
    items = relationship("OrderItem", backref="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    product = relationship("Product")


class AgentLog(Base):
    __tablename__ = "agent_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    detail = Column(Text, default="")
    level = Column(String, default="INFO")
    query_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))


class FraudSignal(Base):
    __tablename__ = "fraud_signals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    signal_type = Column(String, nullable=False)
    triggered = Column(Boolean, default=False)
    checked_at = Column(DateTime, default=lambda: datetime.now(UTC))
    analyst_output = Column(Text, nullable=True)
    decision = Column(String, nullable=True)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)
    severity = Column(String, default="LOW")
    message = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    source_agent = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
