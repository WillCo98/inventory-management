from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    estimated_unit_cost: Optional[float] = None

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

class RestockingRecommendation(BaseModel):
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    demand_gap: int
    unit_cost: float
    recommended_quantity: int
    line_cost: float

class RestockOrderItemRequest(BaseModel):
    item_sku: str
    item_name: str
    quantity: int
    unit_cost: float

class RestockOrderRequest(BaseModel):
    items: List[RestockOrderItemRequest]
    total_value: float

# In-memory storage for submitted restocking orders
submitted_restock_orders: List[dict] = []
restock_order_counter: int = 0

# In-memory storage for tasks (seed with a couple defaults so the UI has content)
tasks_store: List[dict] = [
    {
        "id": "task-100",
        "title": "Confirm Tokyo warehouse cycle count",
        "priority": "high",
        "dueDate": "2026-04-24",
        "status": "pending",
    },
    {
        "id": "task-101",
        "title": "Sign off on Q2 procurement plan",
        "priority": "medium",
        "dueDate": "2026-04-28",
        "status": "pending",
    },
]
task_counter: int = len(tasks_store)

class Task(BaseModel):
    id: str
    title: str
    priority: str
    dueDate: Optional[str] = None
    status: str

class CreateTaskRequest(BaseModel):
    title: str
    priority: str = "medium"
    dueDate: Optional[str] = None

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    # Calculate quarterly statistics from orders
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends():
    """Get month-over-month trends"""
    months = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

@app.get("/api/restocking/recommendations", response_model=List[RestockingRecommendation])
def get_restocking_recommendations(budget: float):
    """Get restocking recommendations based on budget"""
    # Build SKU-to-unit_cost lookup from inventory
    sku_cost_map = {item['sku']: item['unit_cost'] for item in inventory_items}

    # Trend priority: increasing=0, stable=1, decreasing=2
    trend_priority = {'increasing': 0, 'stable': 1, 'decreasing': 2}

    # Build recommendation candidates
    candidates = []
    for forecast in demand_forecasts:
        demand_gap = forecast['forecasted_demand'] - forecast['current_demand']
        if demand_gap <= 0:
            continue

        # Use inventory cost if available, else estimated_unit_cost from forecast
        unit_cost = sku_cost_map.get(forecast['item_sku'], forecast.get('estimated_unit_cost', 50.0))
        line_cost = round(unit_cost * demand_gap, 2)

        candidates.append({
            'item_sku': forecast['item_sku'],
            'item_name': forecast['item_name'],
            'current_demand': forecast['current_demand'],
            'forecasted_demand': forecast['forecasted_demand'],
            'trend': forecast['trend'],
            'demand_gap': demand_gap,
            'unit_cost': unit_cost,
            'recommended_quantity': demand_gap,
            'line_cost': line_cost
        })

    # Sort by trend priority, then demand_gap descending
    candidates.sort(key=lambda x: (trend_priority.get(x['trend'], 9), -x['demand_gap']))

    # Select items that fit within budget
    result = []
    remaining_budget = budget
    for candidate in candidates:
        if candidate['line_cost'] <= remaining_budget:
            result.append(candidate)
            remaining_budget -= candidate['line_cost']

    return result

@app.post("/api/restocking/orders")
def create_restock_order(request: RestockOrderRequest):
    """Submit a restocking order"""
    global restock_order_counter
    restock_order_counter += 1

    # Generate order ID (max existing + 1)
    max_id = max(
        [int(o['id']) for o in orders if o['id'].isdigit()] +
        [int(o['id']) for o in submitted_restock_orders if o['id'].isdigit()] +
        [0]
    )
    new_id = str(max_id + 1)

    now = datetime.now()
    order_number = f"RST-2025-{restock_order_counter:04d}"

    order = {
        'id': new_id,
        'order_number': order_number,
        'customer': 'Internal Restocking',
        'items': [
            {
                'sku': item.item_sku,
                'name': item.item_name,
                'quantity': item.quantity,
                'unit_price': item.unit_cost
            }
            for item in request.items
        ],
        'status': 'Submitted',
        'warehouse': None,
        'category': None,
        'order_date': now.isoformat(),
        'expected_delivery': (now + timedelta(days=14)).isoformat(),
        'total_value': round(request.total_value, 2),
        'actual_delivery': None
    }

    submitted_restock_orders.append(order)
    orders.append(order)
    return order

@app.get("/api/restocking/orders")
def get_restock_orders():
    """Get all submitted restocking orders"""
    return submitted_restock_orders

# ─────────────────────────────────────────────────────────────────────
# Tasks
# ─────────────────────────────────────────────────────────────────────

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get all tasks."""
    return tasks_store

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(payload: CreateTaskRequest):
    """Create a new task."""
    global task_counter
    task_counter += 1
    task = {
        "id": f"task-{task_counter + 100}",
        "title": payload.title,
        "priority": payload.priority,
        "dueDate": payload.dueDate,
        "status": "pending",
    }
    tasks_store.insert(0, task)
    return task

@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    """Delete a task by id."""
    idx = next((i for i, t in enumerate(tasks_store) if t["id"] == task_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    tasks_store.pop(idx)
    return None

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task's completed/pending status."""
    task = next((t for t in tasks_store if t["id"] == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

# ─────────────────────────────────────────────────────────────────────
# Purchase orders
# ─────────────────────────────────────────────────────────────────────

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(payload: CreatePurchaseOrderRequest):
    """Create a purchase order tied to a backlog item."""
    # Reject if backlog item already has a PO
    existing = next((po for po in purchase_orders if po["backlog_item_id"] == payload.backlog_item_id), None)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Backlog item {payload.backlog_item_id} already has a purchase order",
        )
    new_po = {
        "id": f"PO-{2026000 + len(purchase_orders) + 1}",
        "backlog_item_id": payload.backlog_item_id,
        "supplier_name": payload.supplier_name,
        "quantity": payload.quantity,
        "unit_cost": payload.unit_cost,
        "expected_delivery_date": payload.expected_delivery_date,
        "status": "pending",
        "created_date": datetime.utcnow().date().isoformat(),
        "notes": payload.notes,
    }
    purchase_orders.append(new_po)
    return new_po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog(backlog_item_id: str):
    """Get a purchase order for a given backlog item."""
    po = next((po for po in purchase_orders if po["backlog_item_id"] == backlog_item_id), None)
    if po is None:
        raise HTTPException(status_code=404, detail=f"No purchase order for backlog item {backlog_item_id}")
    return po

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
