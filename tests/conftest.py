"""Shared test fixtures — in-memory SQLite, sample data, mock LLM."""
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from commerceos.database.models import Base, Customer, Order, OrderItem, Product


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database with sample data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    products = [
        Product(id="P1001", name="Classic Cotton T-Shirt - Black", category="Apparel",
                price=14.99, stock_quantity=120, reorder_threshold=30),
        Product(id="P1002", name="Classic Cotton T-Shirt - White", category="Apparel",
                price=14.99, stock_quantity=8, reorder_threshold=30),
        Product(id="P1003", name="Wireless Bluetooth Headphones", category="Electronics",
                price=49.99, stock_quantity=25, reorder_threshold=10),
    ]
    for p in products:
        session.add(p)

    customer = Customer(id=1, name="Sarah Ahmed", email="sarah@email.com",
                        account_age_days=412, total_orders=1, total_spent=49.99)
    session.add(customer)

    order = Order(id="O2001", customer_id=1, status="delivered",
                  total_amount=49.99, shipping_address="Pakistan",
                  billing_address="Pakistan", payment_method="Credit Card",
                  created_at=datetime.now(UTC) - timedelta(days=30))
    session.add(order)

    item = OrderItem(order_id="O2001", product_id="P1003", quantity=1, unit_price=49.99)
    session.add(item)

    session.commit()
    yield session
    session.close()
