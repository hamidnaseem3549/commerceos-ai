"""Event-driven workflow definitions."""
from datetime import UTC

from commerceos.observability.activity_tracker import track
from commerceos.orchestration.event_bus import event_bus


def register_event_handlers():
    @event_bus.on("order.created")
    def handle_order_created(data: dict):
        order_id = data.get("order_id", "")
        track("Workflow", "event", f"order.created: {order_id}")

        from commerceos.agents import AgentRegistry
        fraud = AgentRegistry.get("fraud")
        if fraud:
            try:
                result = fraud.run(f"Check order {order_id} for fraud")
                track("Workflow", "fraud_check", f"Order {order_id}: {result['answer'][:60]}")
                if "REJECT" in result["answer"] or "HOLD" in result["answer"]:
                    from commerceos.database.connection import get_session
                    from commerceos.database.models import Alert
                    s = get_session()
                    s.add(Alert(type="fraud_flag",
                                severity="HIGH" if "REJECT" in result["answer"] else "MEDIUM",
                                message=f"Order {order_id} flagged by auto-fraud check",
                                source_agent="Workflow"))
                    s.commit()
                    s.close()
            except Exception as e:  # noqa: BLE001
                track("Workflow", "fraud_error", str(e), level="ERROR")

        from commerceos.database.connection import get_session
        from commerceos.database.models import Order as OrderModel
        from commerceos.database.models import OrderItem, Product
        s = get_session()
        order = s.query(OrderModel).filter(OrderModel.id == order_id).first()
        if order:
            items = s.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            for item in items:
                prod = s.query(Product).filter(Product.id == item.product_id).first()
                if prod:
                    prod.stock_quantity -= item.quantity
                    if prod.stock_quantity <= prod.reorder_threshold:
                        from commerceos.database.models import Alert
                        s.add(Alert(type="low_stock", severity="MEDIUM",
                                    message=f"{prod.name} low ({prod.stock_quantity} left)",
                                    source_agent="Workflow"))
            if order.status == "pending":
                order.status = "confirmed"
                from datetime import datetime
                order.updated_at = datetime.now(UTC)
            s.commit()
        s.close()

    track("Workflow", "init", "Event handlers registered")
