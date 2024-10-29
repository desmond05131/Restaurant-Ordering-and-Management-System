from pydantic import Field
from datetime import datetime,date, timezone, time
from fastapi import Depends, HTTPException, status, Query
from typing import Annotated,Literal,List, Optional
from sqlalchemy import select, and_, func, extract
from PIL import Image
from escpos import cli, printer
import zpl


from root.components.voucher import voucher_base, voucher_requirement_base, create_voucher,apply_voucher
from root.account.get_user_data_from_db import get_role
from root.components.inventory_management import item, inventory
from root.account.account import validate_role
from root.database.database_models import User, Inventory,BatchPackage,InventoryBatch, Order, OrderItem, session, Menu_items, Item_ingredients, CartItem, ShoppingCart, Voucher
from root.database.data_format import *
from api import app


current_time = datetime.now()
formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
print(formatted_time)


def generate_sales_report(year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, float]:
    query = session.query(
        func.count(Order.Order_id).label('number_of_sales'),
        func.sum(Order.NetTotal).label('total_net_total')
    ).filter(extract('year', Order.Time_Placed) == year)

    if month is not None:
        query = query.filter(extract('month', Order.Time_Placed) == month)
    if week is not None:
        query = query.filter(extract('week', Order.Time_Placed) == week)
    if day is not None:
        query = query.filter(extract('day', Order.Time_Placed) == day)

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
    report = {report_key: {"number_of_sales": number_of_sales, "total_net_total": total_net_total}}

    return report

def generate_cost_report(year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, float]:
    query = session.query(
        func.sum(InventoryBatch.Cost).label('total_cost')
    ).filter(extract('year', InventoryBatch.Acquisition_date) == year)

    if month is not None:
        query = query.filter(extract('month', InventoryBatch.Acquisition_date) == month)
    if week is not None:
        query = query.filter(extract('week', InventoryBatch.Acquisition_date) == week)
    if day is not None:
        query = query.filter(extract('day', InventoryBatch.Acquisition_date) == day)

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
    report = {report_key: {"total_cost": total_cost}}

    return report





@app.patch('/orders/checkout', tags=['orders'])
def checkout_order(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))], table_number: int, paying_method: Literal['Cash', 'Credit Card', 'Debit Card', 'E-Wallet']):
    order = session.query(Order).filter(Order.Table_number == table_number).order_by(Order.Time_Placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order.PayingMethod = paying_method
    UserPoints = session.query(User).filter(User.UID == order.UID).first()
    UserPoints.Points += int((order.NetTotal)/10)
    session.commit()

    receipt_info = {
        "table_number": order.Table_number,
        "order_id": order.Order_id,
        "time_placed": order.Time_Placed,
        "voucher_applied": order.VoucherApplied,
        "Subtotal": order.Subtotal,
        "ServiceCharge": order.ServiceCharge,
        "ServiceTax": order.ServiceTax,
        "RoundingAdjustment": order.RoundingAdjustment,
        "NetTotal": order.NetTotal,
        "paying_method": order.PayingMethod,
        "items": []
    }

    order_items = session.query(OrderItem).filter(OrderItem.Order_id == order.Order_id).all()
    for item in order_items:
        receipt_info["items"].append({
            "item_name": item.Item_Name,
            "quantity": item.Quantity,
            "remarks": item.Remarks,
            "status": item.Status
        })
    def generate_receipt(receipt_info):
        instance = printer.Dummy()
        instance.text(f"Table Number: {receipt_info['table_number']}\n")
        instance.text(f"Order ID: {receipt_info['order_id']}\n")
        instance.text(f"Time Placed: {receipt_info['time_placed']}\n")
        instance.text(f"Voucher Applied: {receipt_info['voucher_applied']}\n")
        instance.text(f"Subtotal: {receipt_info['Subtotal']}\n")
        instance.text(f"Service Charge: {receipt_info['ServiceCharge']}\n")
        instance.text(f"Service Tax: {receipt_info['ServiceTax']}\n")
        instance.text(f"Rounding Adjustment: {receipt_info['RoundingAdjustment']}\n")
        instance.text(f"Net Total: {receipt_info['NetTotal']}\n")
        instance.text(f"Paying Method: {receipt_info['paying_method']}\n")
        instance.text("\nItems:\n")
        for item in receipt_info['items']:
            instance.text(f"Item Name: {item['item_name']}\n")
            instance.text(f"Quantity: {item['quantity']}\n")
            instance.text(f"Remarks: {item['remarks']}\n")
            instance.text(f"Status: {item['status']}\n")
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
        l.write_text(f"Net Total: {receipt_info['NetTotal']}", char_height=3, char_width=2, line_width=60, justification='C', font='A')
        l.endorigin()
        l.origin(0, 24)
        l.write_text(f"Paying Method: {receipt_info['paying_method']}", char_height=3, char_width=2, line_width=60, justification='C', font='A')
        l.endorigin()

        with open("./receipt.zpl", "w") as file:
            file.write(l.dumpZPL())

    generate_receipt(receipt_info)

    generate_receipt(receipt_info)
    return {"message": "Order checked out", "receipt": receipt_info, "receipt_files": ["./receipt.bin", "./receipt.zpl"]}


@app.get('/analytics/total_sales', tags=['analytics'])
def get_sales_report(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))],year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, Dict[str, float]]:
    if month is not None and (month < 1 or month > 12):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month value. Month must be between 1 and 12")
    if week is not None and (week < 1 or week > 5):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid week value. Week must be between 1 and 5")
    if day is not None and (day < 1 or day > 31):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid day value. Day must be between 1 and 31")

    report = generate_sales_report(year, month, week, day)
    return {"report": report}

@app.get('/analytics/total_cost', tags=['analytics'])
def get_total_cost_report(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))], year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, Dict[str, float]]:
    if month is not None and (month < 1 or month > 12):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month value. Month must be between 1 and 12")
    if week is not None and (week < 1 or week > 5):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid week value. Week must be between 1 and 5")
    if day is not None and (day < 1 or day > 31):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid day value. Day must be between 1 and 31")

    report = generate_cost_report(year, month, week, day)
    return {"report": report}


@app.get('/analytics/gross_profit', tags=['analytics'])
def get_gross_profit_report(user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))], year: int, month: Optional[int] = None, week: Optional[int] = None, day: Optional[int] = None) -> Dict[str, Dict[str, float]]:
    sales_report = generate_sales_report(year, month, week, day)
    cost_report = generate_cost_report(year, month, week, day)

    gross_profit_report = {}
    for key in sales_report.keys():
        gross_profit_report[key] = {
            "gross_profit": sales_report[key]["total_net_total"] - cost_report[key]["total_cost"]
        }

    return {"report": gross_profit_report}


@app.get('/analytics/popular_items', tags=['analytics'])
def generate_popular_items_report(sort_by: Literal['most_ordered', 'least_ordered', 'highest_ratings', 'lowest_ratings'], item_category: Optional[str] = None):
    query = session.query(
        Menu_items.Item_name,
        func.count(OrderItem.Item_id).label('order_count'),
        func(Menu_items.Ratings).label('average_rating')
    ).join(OrderItem, Menu_items.Item_id == OrderItem.Item_id)

    if item_category:
        query = query.filter(Menu_items.Category == item_category)

    query = query.group_by(Menu_items.Item_name)

    if sort_by == 'most_ordered':
        query = query.order_by(func.count(OrderItem.Item_id).desc())
    elif sort_by == 'least_ordered':
        query = query.order_by(func.count(OrderItem.Item_id).asc())
    elif sort_by == 'highest_ratings':
        query = query.order_by((Menu_items.Ratings).desc())
    elif sort_by == 'lowest_ratings':
        query = query.order_by((Menu_items.Ratings).asc())

    popular_items_data = query.all()

    report = []
    for data in popular_items_data:
        report.append({
            "item_name": data.Item_name,
            "order_count": data.order_count,
            "average_rating": data.Ratings
        })

    return {"report": report}




