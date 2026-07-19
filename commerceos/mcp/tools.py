"""MCP Tool Layer — DB-backed data access for all agents."""
from datetime import timedelta, datetime, timezone
from commerceos.mcp.registry import register_tool, get_tool
from commerceos.database.connection import get_session
from commerceos.database.models import Product, Customer, Order, OrderItem


def get_all_products() -> list[dict]:
    session = get_session()
    products = session.query(Product).all()
    result = [{"product_id": p.id, "product_name": p.name, "category": p.category,
               "price": p.price, "stock_quantity": p.stock_quantity,
               "reorder_threshold": p.reorder_threshold, "image_url": p.image_url,
               "is_on_sale": p.is_on_sale, "sale_price": p.sale_price} for p in products]
    session.close()
    return result


def search_products(query: str) -> list[dict]:
    session = get_session()
    products = session.query(Product).all()
    words = query.lower().split()
    result = []
    for p in products:
        if any(w in p.name.lower() for w in words):
            result.append({"product_id": p.id, "product_name": p.name, "category": p.category,
                           "price": p.price, "stock_quantity": p.stock_quantity,
                           "reorder_threshold": p.reorder_threshold, "image_url": p.image_url,
                           "is_on_sale": p.is_on_sale, "sale_price": p.sale_price})
    session.close()
    return result


def get_low_stock_products() -> list[dict]:
    session = get_session()
    products = session.query(Product).filter(Product.stock_quantity <= Product.reorder_threshold).all()
    result = [{"product_id": p.id, "product_name": p.name, "stock_quantity": p.stock_quantity,
               "reorder_threshold": p.reorder_threshold} for p in products]
    session.close()
    return result


def get_product_by_id(product_id: str) -> dict | None:
    session = get_session()
    p = session.query(Product).filter(Product.id == product_id).first()
    if not p:
        session.close()
        return None
    result = {"product_id": p.id, "product_name": p.name, "category": p.category,
              "price": p.price, "stock_quantity": p.stock_quantity,
              "reorder_threshold": p.reorder_threshold, "image_url": p.image_url,
              "is_on_sale": p.is_on_sale, "sale_price": p.sale_price}
    session.close()
    return result


def get_order_by_id(order_id: str) -> dict | None:
    session = get_session()
    o = session.query(Order).filter(Order.id == order_id.upper()).first()
    if not o:
        session.close()
        return None
    c = session.query(Customer).filter(Customer.id == o.customer_id).first()
    items = session.query(OrderItem).filter(OrderItem.order_id == o.id).all()
    result = {"order_id": o.id, "customer_name": c.name if c else "",
              "customer_email": c.email if c else "", "product_id": items[0].product_id if items else "",
              "order_amount": o.total_amount, "quantity": sum(i.quantity for i in items) if items else 1,
              "order_timestamp": str(o.created_at), "shipping_country": o.shipping_address,
              "billing_country": o.billing_address, "status": o.status,
              "tracking_number": o.tracking_number}
    session.close()
    return result


def get_fraud_signals(order_id: str) -> dict | None:
    session = get_session()
    order = session.query(Order).filter(Order.id == order_id.upper()).first()
    if not order:
        session.close()
        return None
    customer = session.query(Customer).filter(Customer.id == order.customer_id).first()
    if not customer:
        session.close()
        return {"order_id": order_id, "velocity_flag": False, "velocity_count": 0,
                "country_mismatch": False, "new_account_high_value": False,
                "disposable_email": False, "total_flags": 0}

    window_start = order.created_at - timedelta(minutes=15)
    window_end = order.created_at + timedelta(minutes=15)
    nearby = session.query(Order).filter(Order.customer_id == customer.id,
                                         Order.created_at >= window_start,
                                         Order.created_at <= window_end).count()
    velocity_flag = nearby > 1
    country_mismatch = order.shipping_address != order.billing_address if order.shipping_address else False
    new_account_high_value = customer.account_age_days <= 3 and order.total_amount >= 100
    disposable_markers = ["tempmail", "guest", "temp", "10minutemail", "throwaway"]
    disposable_email = any(m in customer.email.lower() for m in disposable_markers)
    total = sum([velocity_flag, country_mismatch, new_account_high_value, disposable_email])
    session.close()
    return {"order_id": order_id, "velocity_flag": velocity_flag, "velocity_count": nearby,
            "country_mismatch": country_mismatch, "new_account_high_value": new_account_high_value,
            "disposable_email": disposable_email, "total_flags": total}


def get_all_flagged_orders() -> list[dict]:
    session = get_session()
    orders = session.query(Order).all()
    flagged = []
    for o in orders:
        sig = get_fraud_signals(o.id)
        if sig and sig["total_flags"] >= 2:
            flagged.append(sig)
    session.close()
    return flagged


_next_order_num = [2016]


def append_order(customer_name: str, customer_email: str, shipping_country: str,
                 product_id: str, quantity: int = 1) -> dict:
    try:
        from commerceos.orchestration.event_bus import event_bus
    except ImportError:
        event_bus = None
    session = get_session()
    try:
        product = session.query(Product).filter(Product.id == product_id).first()
        if not product:
            session.close()
            return {"error": f"Product {product_id} not found"}

        customer = session.query(Customer).filter(Customer.email == customer_email).first()
        if not customer:
            customer = Customer(name=customer_name, email=customer_email, account_age_days=0)
            session.add(customer)
            session.flush()

        order_id = f"O{_next_order_num[0]}"
        _next_order_num[0] += 1
        total = round(product.price * quantity, 2)
        now = datetime.now(timezone.utc)

        order = Order(id=order_id, customer_id=customer.id, status="pending",
                      total_amount=total, shipping_address=shipping_country,
                      billing_address=shipping_country, created_at=now)
        session.add(order)
        session.flush()

        session.add(OrderItem(order_id=order_id, product_id=product_id,
                              quantity=quantity, unit_price=product.price))
        session.commit()

        # Emit event for auto-triggered workflows
        if event_bus:
            try:
                event_bus.emit("order.created", {
                    "order_id": order_id, "customer_email": customer_email,
                    "product_id": product_id, "quantity": quantity,
                })
            except Exception:
                pass

        product_name = product.name
        session.close()
        return {"order_id": order_id, "product_name": product_name, "total": total}
    except Exception as e:
        session.rollback()
        session.close()
        return {"error": str(e)}


# Register all tools
for _name, _func in [
    ("get_all_products", get_all_products), ("search_products", search_products),
    ("get_low_stock_products", get_low_stock_products),
    ("get_product_by_id", get_product_by_id), ("get_order_by_id", get_order_by_id),
    ("get_fraud_signals", get_fraud_signals),
    ("get_all_flagged_orders", get_all_flagged_orders),
    ("append_order", append_order),
]:
    register_tool(_name, _func)


def call_tool(tool_name: str, **kwargs):
    func = get_tool(tool_name)
    if func is None:
        raise ValueError(f"Unknown tool: {tool_name}")
    return func(**kwargs)
