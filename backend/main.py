"""FastAPI backend for CommerceOS AI — wraps the agent engine in REST endpoints."""
import sys
import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# ── CommerceOS imports ──
from commerceos.config import settings
from commerceos.mcp.tools import call_tool
from commerceos.orchestration.supervisor import handle_query
from commerceos.agents.pricing_agent import analyze_and_apply_sales
from commerceos.database.connection import get_session, init_db
from commerceos.database.models import Product, Order, Alert, AgentLog, Customer
from commerceos.agents import AgentRegistry

# ── Startup ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from commerceos.agents import AgentRegistry
    yield

app = FastAPI(title="CommerceOS AI API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic models ──
class ChatRequest(BaseModel):
    query: str
    thread_id: str = "default"

class OrderRequest(BaseModel):
    customer_name: str
    customer_email: str
    shipping_country: str
    product_id: str
    quantity: int = 1

class ChatResponse(BaseModel):
    answer: str
    agent: str
    ops_alert: str = ""
    context_used: str = ""


# ══════════════════════════════════════════════════
#  PRODUCT ENDPOINTS
# ══════════════════════════════════════════════════

@app.get("/api/products")
def get_products(category: Optional[str] = None, search: Optional[str] = None):
    """Get all products, optionally filtered."""
    if search:
        products = call_tool("search_products", query=search)
    else:
        products = call_tool("get_all_products")
    if category:
        products = [p for p in products if p.get("category", "").lower() == category.lower()]
    return {"products": products, "count": len(products)}


@app.get("/api/products/categories")
def get_categories():
    """Get all product categories."""
    products = call_tool("get_all_products")
    cats = sorted(set(p.get("category", "Other") for p in products))
    return {"categories": cats}


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    product = call_tool("get_product_by_id", product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/api/products/low-stock")
def get_low_stock():
    return {"products": call_tool("get_low_stock_products")}


# ══════════════════════════════════════════════════
#  ORDER ENDPOINTS
# ══════════════════════════════════════════════════

@app.post("/api/orders")
def place_order(req: OrderRequest):
    """Place a new order. Auto-triggers fraud check + inventory update."""
    result = call_tool("append_order",
        customer_name=req.customer_name,
        customer_email=req.customer_email,
        shipping_country=req.shipping_country,
        product_id=req.product_id,
        quantity=req.quantity,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/orders/{order_id}")
def get_order(order_id: str):
    order = call_tool("get_order_by_id", order_id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/api/orders")
def get_orders(email: str = Query("", description="Customer email")):
    if not email:
        raise HTTPException(status_code=400, detail="Email parameter required")
    orders = call_tool("get_orders_by_email", email=email)
    return {"orders": orders}


# ══════════════════════════════════════════════════
#  CHAT / AI ASSISTANT ENDPOINT
# ══════════════════════════════════════════════════

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Send a query to the AI supervisor. Returns agent response."""
    result = handle_query(req.query, thread_id=req.thread_id)
    return ChatResponse(
        answer=result.get("answer", ""),
        agent=result.get("agent_name", "System"),
        ops_alert=result.get("ops_alert", ""),
        context_used=result.get("context_used", ""),
    )


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """Stream the AI response via Server-Sent Events."""
    async def event_generator():
        yield {"event": "start", "data": json.dumps({"agent": "analyzing"})}
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, handle_query, req.query, req.thread_id)
        yield {
            "event": "complete",
            "data": json.dumps({
                "answer": result.get("answer", ""),
                "agent": result.get("agent_name", "System"),
                "ops_alert": result.get("ops_alert", ""),
            })
        }
    return EventSourceResponse(event_generator())


# ══════════════════════════════════════════════════
#  ADMIN DASHBOARD ENDPOINTS
# ══════════════════════════════════════════════════

@app.get("/api/admin/stats")
def get_admin_stats():
    """Dashboard metrics."""
    session = get_session()
    stats = {
        "total_orders": session.query(Order).count(),
        "pending_orders": session.query(Order).filter(Order.status == "pending").count(),
        "low_stock_items": session.query(Product).filter(
            Product.stock_quantity <= Product.reorder_threshold
        ).count(),
        "fraud_alerts": session.query(Alert).filter(
            Alert.type == "fraud_flag", Alert.resolved == False
        ).count(),
        "total_customers": session.query(Customer).count(),
        "total_products": session.query(Product).count(),
    }
    session.close()
    return stats


@app.get("/api/admin/alerts")
def get_admin_alerts(limit: int = 20):
    session = get_session()
    alerts = session.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()
    result = [
        {"type": a.type, "severity": a.severity, "message": a.message,
         "source": a.source_agent, "resolved": a.resolved,
         "created_at": str(a.created_at)}
        for a in alerts
    ]
    session.close()
    return {"alerts": result}


@app.get("/api/admin/logs")
def get_admin_logs(limit: int = 50):
    session = get_session()
    logs = session.query(AgentLog).order_by(AgentLog.timestamp.desc()).limit(limit).all()
    result = [
        {"agent": l.agent_name, "action": l.action, "detail": l.detail,
         "level": l.level, "timestamp": str(l.timestamp)}
        for l in logs
    ]
    session.close()
    return {"logs": result}


@app.get("/api/admin/agents")
def get_agents():
    return {"agents": AgentRegistry.list(), "count": len(AgentRegistry.list())}


@app.post("/api/admin/actions/fraud-sweep")
def run_fraud_sweep():
    flagged = call_tool("get_all_flagged_orders")
    return {"flagged": len(flagged), "orders": flagged}


@app.post("/api/admin/actions/stock-check")
def run_stock_check():
    low = call_tool("get_low_stock_products")
    return {"low_stock": len(low), "products": low}


@app.post("/api/admin/actions/pricing-analysis")
def run_pricing_analysis():
    applied = analyze_and_apply_sales()
    return {"sales_applied": len(applied), "products": applied}


# ══════════════════════════════════════════════════
#  HEALTH CHECK
# ══════════════════════════════════════════════════

@app.get("/api/health")
def health():
    return {"status": "ok", "agents": AgentRegistry.list(), "timestamp": str(datetime.now(timezone.utc))}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
