"""MCP Tool Layer — DB-backed data access for all agents."""
from datetime import UTC, datetime, timedelta

from commerceos.database.connection import get_session
from commerceos.database.models import Customer, Order, OrderItem, Product
from commerceos.mcp.registry import get_tool, register_tool


def get_all_products() -> list[dict]:
    """Fetch all products from the database.

    Returns:
        list[dict]: Each product dict contains product_id, product_name,
        category, price, stock_quantity, reorder_threshold, image_url,
        is_on_sale, sale_price.
    """
    session = get_session()
    products = session.query(Product).all()
    result = [{"product_id": p.id, "product_name": p.name, "category": p.category,
               "price": p.price, "stock_quantity": p.stock_quantity,
               "reorder_threshold": p.reorder_threshold, "image_url": p.image_url,
               "is_on_sale": p.is_on_sale, "sale_price": p.sale_price} for p in products]
    session.close()
    return result


def search_products(query: str) -> list[dict]:
    """Search products by keyword matching against product names.

    Args:
        query: Space-separated search terms.

    Returns:
        list[dict]: Matching products (empty list if none match).
    """
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
    """Return products where stock is at or below reorder threshold.

    Returns:
        list[dict]: Low-stock products with product_id, product_name,
        stock_quantity, reorder_threshold.
    """
    session = get_session()
    products = session.query(Product).filter(Product.stock_quantity <= Product.reorder_threshold).all()
    result = [{"product_id": p.id, "product_name": p.name, "stock_quantity": p.stock_quantity,
               "reorder_threshold": p.reorder_threshold} for p in products]
    session.close()
    return result


def get_product_by_id(product_id: str) -> dict | None:
    """Fetch a single product by its ID.

    Args:
        product_id: e.g. ``"P1001"``.

    Returns:
        Product dict, or ``None`` if not found.
    """
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
    """Fetch a single order by its ID.

    Args:
        order_id: e.g. ``"O2001"``.

    Returns:
        Order dict with customer and item details, or ``None``.
    """
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


def get_orders_by_email(email: str) -> list[dict]:
    """Fetch all orders for a given customer email.

    Args:
        email: Customer email address.

    Returns:
        list[dict]: Orders for this customer (empty if none found).
    """
    session = get_session()
    customers = session.query(Customer).filter(Customer.email == email.lower()).all()
    if not customers:
        session.close()
        return []
    customer_ids = [c.id for c in customers]
    orders = session.query(Order).filter(Order.customer_id.in_(customer_ids)).all()
    result = []
    for o in orders:
        items = session.query(OrderItem).filter(OrderItem.order_id == o.id).all()
        result.append({
            "order_id": o.id, "customer_name": customers[0].name,
            "customer_email": email, "product_id": items[0].product_id if items else "",
            "order_amount": o.total_amount, "quantity": sum(i.quantity for i in items) if items else 1,
            "order_timestamp": str(o.created_at), "shipping_country": o.shipping_address,
            "billing_country": o.billing_address, "status": o.status,
        })
    session.close()
    return result


def get_fraud_signals(order_id: str) -> dict | None:
    """Evaluate fraud signals for a specific order.

    Checks: order velocity, country mismatch, new-account high-value,
    and disposable email. An order scores 0-4 signals.

    Args:
        order_id: e.g. ``"O2004"``.

    Returns:
        Dict with signal breakdown and ``total_flags`` count, or
        ``None`` if the order is not found.
    """
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
    """Return all orders with 2+ fraud signals.

    Used by the fraud sweep feature in the admin dashboard and
    by the Fraud Agent for bulk analysis.

    Returns:
        list[dict]: Flagged order signal data.
    """
    session = get_session()
    orders = session.query(Order).all()
    flagged = []
    for o in orders:
        sig = get_fraud_signals(o.id)
        if sig and sig["total_flags"] >= 2:
            flagged.append(sig)
    session.close()
    return flagged


_next_order_num = [2016]  # Will be auto-corrected on first call


def _get_next_order_id() -> str:
    """Get the next available order ID by checking the database."""
    from commerceos.database.connection import get_session
    from commerceos.database.models import Order as OrderModel
    session = get_session()
    try:
        highest = session.query(OrderModel.id).order_by(OrderModel.id.desc()).first()
        if highest and highest[0].startswith("O"):
            num = int(highest[0][1:]) + 1
            _next_order_num[0] = max(_next_order_num[0], num)
    except Exception:  # noqa: BLE001, S110
        pass
    finally:
        session.close()
    order_id = f"O{_next_order_num[0]}"
    _next_order_num[0] += 1
    return order_id


def append_order(customer_name: str, customer_email: str, shipping_country: str,
                 product_id: str, quantity: int = 1) -> dict:
    """Place a new order and emit ``order.created`` event.

    Creates the customer if they don't exist, deducts nothing yet
    (event handlers handle inventory), and returns the new order details.
    The event bus triggers fraud check + inventory deduction + alerts.

    Args:
        customer_name: Full name of the customer.
        customer_email: Email address (looked up or created).
        shipping_country: Destination country.
        product_id: SKU being ordered.
        quantity: Number of units.

    Returns:
        Dict with ``order_id``, ``product_name``, and ``total``,
        or ``{"error": "..."}`` on failure.
    """
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

        order_id = _get_next_order_id()
        total = round(product.price * quantity, 2)
        now = datetime.now(UTC)

        order = Order(id=order_id, customer_id=customer.id, status="pending",
                      total_amount=total, shipping_address=shipping_country,
                      billing_address=shipping_country, created_at=now)
        session.add(order)
        session.flush()

        session.add(OrderItem(order_id=order_id, product_id=product_id,
                              quantity=quantity, unit_price=product.price))
        product_name = product.name  # Capture before session closes
        session.commit()
        session.close()

        # Emit event AFTER session close so event handlers get their own session
        if event_bus:
            try:
                event_bus.emit("order.created", {
                    "order_id": order_id, "customer_email": customer_email,
                    "product_id": product_id, "quantity": quantity,
                })
            except Exception:  # noqa: BLE001, S110
                pass

        return {"order_id": order_id, "product_name": product_name, "total": total}
    except Exception as e:  # noqa: BLE001
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
    ("get_orders_by_email", get_orders_by_email),
    ("append_order", append_order),
]:
    register_tool(_name, _func)


def call_tool(tool_name: str, **kwargs):
    func = get_tool(tool_name)
    if func is None:
        raise ValueError(f"Unknown tool: {tool_name}")
    return func(**kwargs)
