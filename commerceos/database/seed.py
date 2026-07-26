"""Seed the database from CSV source files."""
import os
from datetime import UTC, datetime

import pandas as pd

from commerceos.database.connection import get_session, init_db
from commerceos.database.models import Customer, Order, OrderItem, Product

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
PRODUCTS_CSV = os.path.join(PROJECT_DIR, "data", "products.csv")
ORDERS_CSV = os.path.join(PROJECT_DIR, "data", "orders.csv")


def seed_database():
    init_db()
    session = get_session()

    if session.query(Product).count() > 0:
        print("Database already seeded, skipping.")
        session.close()
        return

    print("Seeding products...")
    products_df = pd.read_csv(PRODUCTS_CSV)
    for _, row in products_df.iterrows():
        session.add(Product(
            id=row["product_id"], name=row["product_name"],
            category=row["category"], price=float(row["price"]),
            stock_quantity=int(row["stock_quantity"]),
            reorder_threshold=int(row["reorder_threshold"]),
            image_url=f"product_{row['product_id'].lower()}.svg",
        ))
    session.commit()
    print(f"  Seeded {len(products_df)} products.")

    print("Seeding orders...")
    orders_df = pd.read_csv(ORDERS_CSV)
    orders_df["order_timestamp"] = pd.to_datetime(orders_df["order_timestamp"])
    order_count = 0

    for _, row in orders_df.iterrows():
        customer = session.query(Customer).filter(Customer.email == row["customer_email"]).first()
        if not customer:
            customer = Customer(name=row["customer_name"], email=row["customer_email"],
                                account_age_days=int(row.get("customer_account_age_days", 0)))
            session.add(customer)
            session.flush()

        if session.query(Order).filter(Order.id == row["order_id"]).first():
            continue

        amount = float(row["order_amount"])
        order = Order(
            id=row["order_id"], customer_id=customer.id, status="delivered",
            total_amount=amount, shipping_address=row.get("shipping_country", ""),
            billing_address=row.get("billing_country", ""),
            payment_method=row.get("payment_method", "Credit Card"),
            created_at=row["order_timestamp"].to_pydatetime(),
        )
        session.add(order)
        session.flush()

        session.add(OrderItem(order_id=order.id, product_id=row["product_id"],
                              quantity=int(row.get("quantity", 1)), unit_price=amount))
        customer.total_orders = (customer.total_orders or 0) + 1
        customer.total_spent = (customer.total_spent or 0) + amount
        order_count += 1

    # ── Demo showcase data ──
    seed_demo_data(session)

    session.commit()
    session.close()
    print(f"  Seeded {order_count} orders.")
    print("Seeding complete.")


def seed_demo_data(session):
    """Seed fraud signals for portfolio demo.

    Adds FraudSignal records for order O2004 so the admin dashboard
    shows real fraud alerts on first launch.
    """
    from commerceos.database.models import FraudSignal

    existing = session.query(FraudSignal).count()
    if existing == 0:
        print("Seeding demo fraud signals...")
        fraud_signals_data = [
            FraudSignal(order_id="O2004", signal_type="velocity", triggered=True,
                        checked_at=datetime(2026, 6, 26, 2, 15, tzinfo=UTC)),
            FraudSignal(order_id="O2004", signal_type="country_mismatch", triggered=True,
                        checked_at=datetime(2026, 6, 26, 2, 15, tzinfo=UTC)),
            FraudSignal(order_id="O2004", signal_type="disposable_email", triggered=True,
                        checked_at=datetime(2026, 6, 26, 2, 15, tzinfo=UTC)),
            FraudSignal(order_id="O2004", signal_type="new_account_high_value", triggered=True,
                        checked_at=datetime(2026, 6, 26, 2, 15, tzinfo=UTC)),
        ]
        for fs in fraud_signals_data:
            session.add(fs)
        session.commit()
        print("  Seeded demo fraud signals for O2004.")


if __name__ == "__main__":
    seed_database()
