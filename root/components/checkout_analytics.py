from datetime import datetime
from fastapi import Depends, HTTPException, status
from typing import Annotated, Dict,Literal,Optional
from sqlalchemy import func, extract
from escpos import printer
import zpl


from root.account.account import validate_role
from root.database.database_models import User,Machine, InventoryBatch, Order, OrderItem, session, MenuItem

from api import app


current_time = datetime.now()
formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
print(formatted_time)


def generate_sales_report(year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, float]:
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

def generate_inventory_cost_report(year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, float]:
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

def generate_machine_cost_report(year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, float]:
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
    order = session.query(Order).filter(Order.table_number == table_number).order_by(Order.time_placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order.paying_method = paying_method
    user_points = session.query(User).filter(User.user_id == order.user_id).first()
    user_points.points += int((order.net_total)/10)
    session.commit()

    receipt_info = {
        "table_number": order.table_number,
        "order_id": order.order_id,
        "time_placed": order.time_placed,
        "voucher_applied": order.voucher_applied,
        "subtotal": order.subtotal,
        "service_charge": order.service_charge,
        "service_tax": order.service_tax,
        "rounding_adjustment": order.rounding_adjustment,
        "net_total": order.net_total,
        "paying_method": order.paying_method,
        "items": []
    }

    order_items = session.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
    for order_item in order_items:
        receipt_info["items"].append({
            "item_name": order_item.item_name,
            "quantity": order_item.quantity,
            "remarks": order_item.remarks,
            "status": order_item.status
        })
    def generate_receipt(receipt_info):
        instance = printer.Dummy()
        instance.text(f"Table Number: {receipt_info['table_number']}\n")
        instance.text(f"Order ID: {receipt_info['order_id']}\n")
        instance.text(f"Time Placed: {receipt_info['time_placed']}\n")
        instance.text(f"Voucher Applied: {receipt_info['voucher_applied']}\n")
        instance.text(f"Subtotal: {receipt_info['subtotal']}\n")
        instance.text(f"Service Charge: {receipt_info['service_charge']}\n")
        instance.text(f"Service Tax: {receipt_info['service_tax']}\n")
        instance.text(f"Rounding Adjustment: {receipt_info['rounding_adjustment']}\n")
        instance.text(f"Net Total: {receipt_info['net_total']}\n")
        instance.text(f"Paying Method: {receipt_info['paying_method']}\n")
        instance.text("\nItems:\n")
        for receipt_item in receipt_info['items']:
            instance.text(f"Item Name: {receipt_item['item_name']}\n")
            instance.text(f"Quantity: {receipt_item['quantity']}\n")
            instance.text(f"Remarks: {receipt_item['remarks']}\n")
            instance.text(f"Status: {receipt_item['status']}\n")
            instance.text("\n")
        instance.cut()
        with open("./receipt.bin", "wb") as file:
            file.write(instance.output)

        l = zpl.Label(100, 60, dpmm=6)
        l.origin(0, 4)
        l.write_text('Restaurant Receipt', char_height=6, char_width=4, line_width=60, justification='C')
        l.endorigin()
        l.origin(0, 12)
        l.write_text(f"Table Number: {receipt_info['table_number']}", char_height=3, char_width=2, line_width=60, justification='C', font='A')
        l.endorigin()
        l.origin(0, 15)
        l.write_text(f"Order ID: {receipt_info['order_id']}", char_height=3, char_width=2, line_width=60, justification='C', font='A')
        l.endorigin()
        l.origin(0, 18)
        l.write_text(f"Time Placed: {receipt_info['time_placed']}", char_height=3, char_width=2, line_width=60, justification='C', font='A')
        l.endorigin()
        l.origin(0, 21)
        l.write_text(f"Net Total: {receipt_info['net_total']}", char_height=3, char_width=2, line_width=60, justification='C', font='A')
        l.endorigin()
        l.origin(0, 24)
        l.write_text(f"Paying Method: {receipt_info['paying_method']}", char_height=3, char_width=2, line_width=60, justification='C', font='A')
        l.endorigin()

        with open("./receipt.zpl", "w") as file:
            file.write(l.dumpZPL())

    generate_receipt(receipt_info)

    generate_receipt(receipt_info)
    return {"message": "Order checked out", "receipt": receipt_info, "receipt_files": ["./receipt.bin", "./receipt.zpl"]}


@app.get('/analytics/total_sales', tags=['Analytics'])
def get_sales_report(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))],year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, Dict[str,  Dict[str, float]]]:
    if month is not None and (month < 1 or month > 12):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month value. Month must be between 1 and 12")
    if week is not None and (week < 1 or week > 5):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid week value. Week must be between 1 and 5")
    if day is not None and (day < 1 or day > 31):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid day value. Day must be between 1 and 31")

    report = generate_sales_report(year, month, week, day)
    return {"report": report}

@app.get('/analytics/total_cost', tags=['Analytics'])
def get_total_cost_report(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))], year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, Dict[str,  Dict[str, float]]]:
    if month is not None and (month < 1 or month > 12):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month value. Month must be between 1 and 12")
    if week is not None and (week < 1 or week > 5):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid week value. Week must be between 1 and 5")
    if day is not None and (day < 1 or day > 31):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid day value. Day must be between 1 and 31")

    report = generate_inventory_cost_report(year, month, week, day)
    return {"report": report}

@app.get('/analytics/machine_cost', tags=['Analytics'])
def get_machine_cost_report(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))], year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, Dict[str,  Dict[str, float]]]:
    if month is not None and (month < 1 or month > 12):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month value. Month must be between 1 and 12")
    if week is not None and (week < 1 or week > 5):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid week value. Week must be between 1 and 5")
    if day is not None and (day < 1 or day > 31):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid day value. Day must be between 1 and 31")

    report = generate_machine_cost_report(year, month, week, day)
    return {"report": report}


@app.get('/analytics/gross_profit', tags=['Analytics'])
def get_gross_profit_report(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))], year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, Dict[str, Dict[str, float]]]:
    sales_report = generate_sales_report(year, month, week, day)
    inventory_cost_report = generate_inventory_cost_report(year, month, week, day)
    machine_cost_report = generate_machine_cost_report(year, month, week, day)

    gross_profit_report = {}
    for key in sales_report.keys():
        gross_profit_report[key] = {
            "gross_profit": sales_report[key]["total_net_total"] - inventory_cost_report[key]["total_cost"] - machine_cost_report[key]["total_cost"]
        }

    return {"report": gross_profit_report}


@app.get('/analytics/popular_items', tags=['Analytics'])
def generate_popular_items_report(sort_by: Literal['most_ordered', 'least_ordered', 'highest_ratings', 'lowest_ratings'], item_category: Optional[str] = None):
    query = session.query(
        MenuItem.item_name,
        func.count(OrderItem.item_id).label('order_count'),
        func.avg(MenuItem.ratings).label('average_rating')
    ).join(OrderItem, MenuItem.item_id == OrderItem.item_id)

    if item_category:
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




