from datetime import datetime
from fastapi import Depends, HTTPException, status
from typing import Annotated, Dict,Literal,Optional
from sqlalchemy import func, extract
from escpos import printer
import zpl


from root.account.account import validate_role
from root.database.database_models import User,Machine, InventoryBatch, Order, OrderItem, session, MenuItem
from root.components.generate_receipt import generate_receipt
from root.components.generate_chart import generate_gross_profit_report, generate_inventory_cost_report, generate_sales_report,generate_machine_cost_report,plot_gross_profit_report,plot_inventory_cost_report,plot_sales_report,plot_machine_cost_report
from api import app


current_time = datetime.now()
formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
print(formatted_time)


def calculate_total_sales(year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, float]:
    query = session.query(
        func.count(Order.order_id).label('number_of_sales'),
        func.sum(Order.net_total).label('total_net_total')
    ).filter(extract('year', Order.time_placed) == year)

    if month is not None:
        query = query.filter(extract('month', Order.time_placed) == month)
    if week is not None:
        query = query.filter(extract('week', Order.time_placed) == week)
    if day is not None:
        query = query.filter(extract('day', Order.time_placed) == day)

    sales = query.all()
    if not sales:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sales data found for the given timeframe")

    report_key = f"{year}"
    if month is not None:
        report_key += f"-{month:02d}"
    if week is not None:
        report_key += f"-W{week:02d}"
    if day is not None:
        report_key += f"-{day:02d}"

    number_of_sales, total_net_total = sales[0]
    report = {report_key: {"number_of_sales": number_of_sales if number_of_sales is not None else 0, "total_net_total": total_net_total if total_net_total is not None else 0}}

    return report

def calculate_total_inventory_cost(year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, float]:
    query = session.query(
        func.sum(InventoryBatch.cost).label('total_cost')
    ).filter(extract('year', InventoryBatch.acquisition_date) == year)

    if month is not None:
        query = query.filter(extract('month', InventoryBatch.acquisition_date) == month)
    if week is not None:
        query = query.filter(extract('week', InventoryBatch.acquisition_date) == week)
    if day is not None:
        query = query.filter(extract('day', InventoryBatch.acquisition_date) == day)

    costs = query.all()
    if not costs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No cost data found for the given timeframe")

    report_key = f"{year}"
    if month is not None:
        report_key += f"-{month:02d}"
    if week is not None:
        report_key += f"-W{week:02d}"
    if day is not None:
        report_key += f"-{day:02d}"

    total_cost = costs[0][0] 
    report = {report_key: {"total_cost": total_cost if total_cost is not None else 0}}

    return report

def calculate_total_machine_cost(year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, float]:
    query = session.query(
        func.sum(Machine.cost).label('total_cost')
    ).filter(extract('year', Machine.acquisition_date) == year)

    if month is not None:
        query = query.filter(extract('month', Machine.acquisition_date) == month)
    if week is not None:
        query = query.filter(extract('week', Machine.acquisition_date) == week)
    if day is not None:
        query = query.filter(extract('day', Machine.acquisition_date) == day)

    costs = query.all()
    if not costs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No cost data found for the given timeframe")

    report_key = f"{year}"
    if month is not None:
        report_key += f"-{month:02d}"
    if week is not None:
        report_key += f"-W{week:02d}"
    if day is not None:
        report_key += f"-{day:02d}"

    total_cost = costs[0][0]
    report = {report_key: {"total_cost": total_cost if total_cost is not None else 0}}

    return report

@app.patch('/orders/checkout', tags=['Orders'])
def checkout_order(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))], table_number: int, paying_method: Literal['Cash', 'Credit Card', 'Debit Card', 'E-Wallet']):
    order = session.query(Order).filter(Order.table_id == table_number).order_by(Order.time_placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.paying_method != 'Not Paid Yet':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order already checked out")

    order.paying_method = paying_method
    user_points = session.query(User).filter(User.user_id == order.user_id).first()
    user_points.points += int((order.net_total)/10)
    session.commit()

    
    receipt_info = {
        "invoice_number": order.order_id,
        "date_time": order.time_placed,
        "table_number": order.table_number.table_id,
        "items": [],
        "voucher_applied": order.user_voucher.voucher.voucher_code if order.user_voucher else None,
        "subtotal": order.subtotal,
        "sales_tax": order.service_charge,
        "service_charge": order.service_tax,
        "rounding_adjustment": order.rounding_adjustment,
        "net_total": order.net_total,
        "paying_method": order.paying_method,
    }

    order_items = session.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
    for order_item in order_items:
        receipt_info["items"].append({
            "quantity": order_item.quantity,
            "name": order_item.item_name,
            "price": session.query(MenuItem).filter(MenuItem.item_id == order_item.item_id).first().price
        })

    # Generate the receipt
    receipt_label = generate_receipt(receipt_info)

    # Print the ZPL code
    print(receipt_label.dumpZPL())

    # Preview the label
    receipt_label.preview()
    return {"message": "Order checked out", "receipt": receipt_info, "receipt_files": ["./receipt.bin", "./receipt.zpl"]}


@app.get('/analytics/total_sales', tags=['Analytics'])
def get_total_sales(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))],year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, Dict[str,  Dict[str, float]]]:
    if month is not None and (month < 1 or month > 12):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month value. Month must be between 1 and 12")
    if week is not None and (week < 1 or week > 5):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid week value. Week must be between 1 and 5")
    if day is not None and (day < 1 or day > 31):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid day value. Day must be between 1 and 31")

    report = calculate_total_sales(year, month, week, day)
    return {"report": report}

@app.get('/analytics/total_cost', tags=['Analytics'])
def get_total_inventory_cost(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))], year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, Dict[str,  Dict[str, float]]]:
    if month is not None and (month < 1 or month > 12):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month value. Month must be between 1 and 12")
    if week is not None and (week < 1 or week > 5):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid week value. Week must be between 1 and 5")
    if day is not None and (day < 1 or day > 31):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid day value. Day must be between 1 and 31")

    report = calculate_total_inventory_cost(year, month, week, day)
    return {"report": report}

@app.get('/analytics/machine_cost', tags=['Analytics'])
def get_total_machine_cost(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))], year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, Dict[str,  Dict[str, float]]]:
    if month is not None and (month < 1 or month > 12):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month value. Month must be between 1 and 12")
    if week is not None and (week < 1 or week > 5):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid week value. Week must be between 1 and 5")
    if day is not None and (day < 1 or day > 31):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid day value. Day must be between 1 and 31")

    report = calculate_total_machine_cost(year, month, week, day)
    return {"report": report}


@app.get('/analytics/gross_profit', tags=['Analytics'])
def get_total_gross_profit(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))], year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, Dict[str, Dict[str, float]]]:
    sales_report = calculate_total_sales(year, month, week, day)
    inventory_cost_report = calculate_total_inventory_cost(year, month, week, day)
    machine_cost_report = calculate_total_machine_cost(year, month, week, day)

    gross_profit_report = {}
    for key in sales_report.keys():
        gross_profit_report[key] = {
            "gross_profit": sales_report[key]["total_net_total"] - inventory_cost_report[key]["total_cost"] - machine_cost_report[key]["total_cost"]
        }

    return {"report": gross_profit_report}


@app.get('/analytics/popular_items', tags=['Analytics'])
def generate_popular_items(sort_by: Literal['most_ordered', 'least_ordered', 'highest_ratings', 'lowest_ratings'], item_category: Optional[Literal['All','Brunch/Breakfast','Rice','Noodle','Italian','Main Courses','Sides','Signature Dishes','Vegan','Dessert','Beverages']] = None):
    query = session.query(
        MenuItem.item_name,
        func.count(OrderItem.item_id).label('order_count'),
        func.avg(MenuItem.ratings).label('average_rating')
    ).join(OrderItem, MenuItem.item_id == OrderItem.item_id)

    if item_category is not None and item_category != 'All':
        query = query.filter(MenuItem.category == item_category)

    query = query.group_by(MenuItem.item_name)

    if sort_by == 'most_ordered':
        query = query.order_by(func.count(OrderItem.item_id).desc())
    elif sort_by == 'least_ordered':
        query = query.order_by(func.count(OrderItem.item_id).asc())
    elif sort_by == 'highest_ratings':
        query = query.order_by((MenuItem.ratings).desc())
    elif sort_by == 'lowest_ratings':
        query = query.order_by((MenuItem.ratings).asc())

    popular_items_data = query.all()

    report = []
    for data in popular_items_data:
        report.append({
            "item_name": data.item_name,
            "order_count": data.order_count,
            "average_rating": data.average_rating
        })

    return {"report": report}

@app.get('/analytics/sales_report', tags=['Analytics'])
def get_sales_report(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))], time_period: Literal["year", "month", "week", "day"], start_time: str, end_time: str) -> Dict[str, Dict[str, Dict[str, float]]]:
    try:
        start_time = datetime.strptime(start_time, "%Y-%m-%d")
        end_time = datetime.strptime(end_time, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD")
    
    report = generate_sales_report(time_period, start_time, end_time)
    graph = plot_sales_report(report, time_period)
    return {"message": "Sales report generated", "report": report, "graph": graph}


@app.get('/analytics/inventory_cost_report', tags=['Analytics'])
def get_inventory_cost_report(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))], time_period: Literal["year", "month", "week", "day"], start_time: str, end_time: str) -> Dict[str, Dict[str, Dict[str, float]]]:
    try:
        start_time = datetime.strptime(start_time, "%Y-%m-%d")
        end_time = datetime.strptime(end_time, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD")
    
    report = generate_inventory_cost_report(time_period, start_time, end_time)
    graph = plot_inventory_cost_report(report, time_period)
    return {"message": "Inventory cost report generated", "report": report, "graph": graph}


@app.get('/analytics/machine_cost_report', tags=['Analytics'])
def get_machine_cost_report(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))], time_period: Literal["year", "month", "week", "day"], start_time: str, end_time: str) -> Dict[str, Dict[str, Dict[str, float]]]:
    try:
        start_time = datetime.strptime(start_time, "%Y-%m-%d")
        end_time = datetime.strptime(end_time, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD")
    
    report = generate_machine_cost_report(time_period, start_time, end_time)
    graph = plot_machine_cost_report(report, time_period)
    return {"message": "Machine cost report generated", "report": report, "graph": graph}


@app.get('/analytics/gross_profit_report', tags=['Analytics'])
def get_gross_profit_report(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))], time_period: Literal["year", "month", "week", "day"], start_time: str, end_time: str) -> Dict[str, Dict[str, Dict[str, float]]]:
    try:
        start_time = datetime.strptime(start_time, "%Y-%m-%d")
        end_time = datetime.strptime(end_time, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD")
    
    report = generate_gross_profit_report(time_period, start_time, end_time)
    graph = plot_gross_profit_report(report, time_period)
    return {"message": "Gross profit report generated", "report": report, "graph": graph}




