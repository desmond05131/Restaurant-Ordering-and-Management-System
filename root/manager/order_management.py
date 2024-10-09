from pydantic import BaseModel
from datetime import datetime
from fastapi import Depends, HTTPException, status
from typing import Annotated
from sqlalchemy.orm import Session
from root.account.account import validate_role
from root.database.database_models import User, Inventory, Order, OrderItem, session
from api import app


class OrderDetails(BaseModel):
    UID: int
    Order_id: int
    Status: str
    Total_Ammount: float
    Time_placed: datetime

class UpdateStatus(BaseModel):
    Order_id: int
    New_status: str

@app.get('/orders/view/{order_id}', response_model= OrderDetails, tags=['orders'])
def view_order_details(order_id: int, user: Annotated[User, Depends(validate_role(roles=['Manager', 'Chef']))]):
    order = session.query(Order).filter_by(Order_ID=order_id).one()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_items = session.query(OrderItem).filter_by(Order_ID=order.Order_ID).all()
    items = [{"product_name": item.Product_Name, "quantity": item.Quantity} for item in order_items]

    customer = session.query(User).filter_by(UID=order.UID).one()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    return {
        "order_id": order.Order_ID,
        "customer_name": customer.Username,
        "order_items": items,
        "total_amount": order.Total_Ammount,
        "time_placed": order.Time_Placed,
        "status": order.Status
    }

@app.patch('/orders/update-status', tags=['orders'])
def update_order_status(user: Annotated[User, Depends(validate_role(roles=['Manager', 'Chef']))],status_update: UpdateStatus):
    order = session.query(Order).filter_by(Order_ID=status_update.order_id).one()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if status_update.new_status not in ['In Progress', 'Completed', 'Cancelled']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order status")

    order.Status = status_update.new_status
    session.commit()

    return {"message": f"Order {status_update.order_id} updated to {status_update.new_status}"}

@app.get('/orders/history', tags=['orders'])
def get_order_history(user: Annotated[User, Depends(validate_role(roles=['Manager']))], start_date: datetime, end_date: datetime):
    orders = session.query(Order).filter(Order.Time_Placed.between(start_date, end_date)).all()

    if not orders:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No orders found in the given date range")

    order_history = []
    for order in orders:
        order_items = session.query(OrderItem).filter_by(Order_ID=order.Order_ID).all()
        items = [{"product_name": item.Product_Name, "quantity": item.Quantity} for item in order_items]

        customer = session.query(User).filter_by(UID=order.UID).one()
        if not customer:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

        order_history.append({
            "order_id": order.Order_ID,
            "customer_name": customer.Username,
            "order_items": items,
            "total_amount": order.Total_Ammount,
            "time_placed": order.Time_Placed,
            "status": order.Status
        })

    return order_history