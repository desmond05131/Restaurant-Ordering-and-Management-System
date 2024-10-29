from pydantic import BaseModel, Field
from datetime import datetime,date, timezone, time, timedelta
from fastapi import Depends, HTTPException, status, Query
from fastapi_utils.tasks import repeat_every
from typing import Annotated,Literal,List, Optional
from sqlalchemy import select, and_, func

from root.components.voucher import voucher_base, voucher_requirement_base, create_voucher,apply_voucher
from root.account.get_user_data_from_db import get_role
from root.components.inventory_management import item, inventory
from root.account.account import validate_role
from root.database.database_models import User, Inventory, Order, OrderItem, session,UserItemRating,UserOverallFeedback, Menu_items,Item_ingredients, CartItem, ShoppingCart, Voucher
from root.database.data_format import *
from api import app


def create_cart(cart_info: shopping_cart):
    cart = session.query(ShoppingCart).filter(ShoppingCart.Table_id == cart_info.Table_number).filter(ShoppingCart.Status == 'Active').one_or_none()
    if cart:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Table already has an active cart,please ask the waiter for assistance")
   
    new_cart = ShoppingCart(
        UID = cart_info.UID,
        Table_number = cart_info.Table_number,
        Creation_time = datetime.now(),
        VoucherApplied = 0,
        Total_Amount = 0.0,
        Status = 'Active',
        LastUpdate = datetime.now()
    )

    session.add(new_cart)
    session.commit()
    session.flush(new_cart)
    return new_cart

def cart_add_item(item: cart_item):
    cart_item = CartItem(
        Item_id = item.Item_id,
        Cart_id = item.Cart_id,
        Item_Name = item.Item_Name,
        Quantity = item.Quantity,
        Remarks = item.Remarks,
        Price = item.Price,
        Added_time = datetime.now()
    )

    session.add(cart_item)
    session.commit()
    session.flush(cart_item)
    return cart_item

def calculate_subtotal(cart_id: int):
    cart = session.query(ShoppingCart).filter(ShoppingCart.Cart_id == cart_id).one()
    cart_items = session.query(CartItem).filter(CartItem.Cart_id == cart_id).all()
    Subtotal = 0.0
    for item in cart_items:
        Subtotal += item.Quantity * item.Price

    cart.Subtotal = Subtotal
    session.commit()

    return cart.Subtotal

def calculate_net_total(cart_id: int):
    cart = session.query(ShoppingCart).filter(ShoppingCart.Cart_id == cart_id).one()
    cart.ServiceCharge = cart.Subtotal * 0.06
    cart.ServiceTax = cart.Subtotal * 0.06
    cart.NetTotal = cart.Subtotal + cart.ServiceCharge + cart.ServiceTax
    net_total_str = f"{cart.NetTotal:.2f}"
    second_decimal = int(net_total_str[-1])
    if second_decimal in {1, 2, 3, 4}:
        cart.NetTotal = round(cart.NetTotal, 1) + 0.05
    elif second_decimal in {6, 7, 8, 9}:
        cart.NetTotal = round(cart.NetTotal, 1) + 0.10

    cart.NetTotal = round(cart.NetTotal, 2)
    cart.RoundingAdjustment = cart.NetTotal - (cart.Subtotal + cart.ServiceCharge + cart.ServiceTax)
    session.commit()

    return cart.NetTotal


def SubmitOrder(order_info: order_created, items: items_in_cart):
    new_order = Order(
        UID = order_info.UID,
        Table_number = order_info.Table_number,
        Time_Placed = datetime.now(),
        VoucherApplied = order_info.VoucherApplied,
        Subtotal = order_info.Subtotal,
        ServiceCharge = order_info.ServiceCharge,
        ServiceTax = order_info.ServiceTax,
        RoundingAdjjustment = order_info.RoundingAdjjustment,
        NetTotal = order_info.NetTotal,
        PayingMethod = 'Not Paid Yet'
    )

    session.add(new_order)
    session.commit()
    session.flush(new_order)

    for item in items.items:
        order_item = OrderItem(
            Order_id = new_order.Order_id,
            Item_id = item.Item_id,
            Item_Name = item.Item_Name,
            Quantity = item.Quantity,
            Remarks = item.Remarks,
            Status = 'Order Received'
        )

        session.add(order_item)
        session.commit()

    return new_order.Order_id


def get_order(order_id: int):
    return session.query(Order).filter(Order.Order_id ==order_id).one()

def delete_all_order():
    session.query(Order).delete()
    session.query(OrderItem).delete()
    session.commit()


@app.get('/menu/view', tags=['menu'])
async def view_menu_items(user: Annotated[User, Depends(validate_role(roles=['manager', 'chef', 'cashier', 'customer']))], search_keyword: str = None) -> List[Get_item]:

    if get_role(user.UID) in ['manager', 'chef']:
        if search_keyword:
            search_keyword = f"%{search_keyword}%"
            query = session.query(Menu_items).where(
                Menu_items.Item_name.ilike(search_keyword) |
                Menu_items.Description.ilike(search_keyword) |
                Menu_items.Category.ilike(search_keyword)
            )
        else:
            query = session.query(Menu_items)
        
        items = []

        for row in query.all():

            row_dict = {}
            row_dict["ingredients"] = []

            row_dict["Item_id"] = row.Item_id
            row_dict["Item_name"] = row.Item_name
            row_dict["Price"] = row.Price
            row_dict["Description"] = row.Description
            row_dict["Category"] = row.Category
            row_dict["Picture_link"] = row.Picture_link

            for inventory in session.execute(
                    select(
                        Item_ingredients.Inventory_id, Item_ingredients.quantity
                    ).where(
                        row.Item_id == Item_ingredients.Item_id
                    )).all():

                ingredient_row = session.execute(
                    select(
                        Inventory.Inventory_name,
                        Inventory.Unit
                    ).where(
                        Inventory.Inventory_id == inventory.Inventory_id
                    )).one()

                row_dict["ingredients"].append({
                    "name": ingredient_row.Inventory_name,
                    "unit": ingredient_row.Unit,
                    "quantity": inventory.quantity
                })

            items.append(Get_item(**row_dict))

        return items
    else:
        items = []

        for item in session.query(Menu_items).order_by(Menu_items.Item_id).all():
            items.append(Get_item(
                Item_id = item.Item_id,
                Item_name = item.Item_name,
                Price = item.Price,
                Description = item.Description,
                Category = item.Category,
                Picture_link = item.Picture_link
            ))

        return items

@app.patch('/cart/add-item', tags=['cart'])
def add_items_to_cart(item: add_item_to_cart,table_number: int, user: Annotated[User, Depends(validate_role(roles=['customer','manager']))]):
    UID = user.UID
    cart = session.query(ShoppingCart).filter(ShoppingCart.UID == UID).filter(ShoppingCart.Status == 'Active').one()
    if not cart:
        create_cart(shopping_cart(UID=UID, Table_number=table_number, Status='Active'))

    item_price = session.query(Menu_items).filter(Menu_items.Item_id == item.Item_id).one().Price
    cart_item = cart_add_item(cart_item(**item.model_dump(), Cart_id=cart.Cart_id, Price=item_price))
    

    session.commit()
    
    return {"message": f"Item {cart_item.Item_Name} added to cart"}

@app.patch('/cart/remove-item', tags=['cart'])
def remove_item_from_cart(item_id: int, user: Annotated[User, Depends(validate_role(roles=['customer','manager']))]):
    UID = user.UID
    cart = session.query(ShoppingCart).filter(ShoppingCart.UID == UID).filter(ShoppingCart.Status == 'Active').one()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    cart_item = session.query(CartItem).filter(CartItem.Item_id == item_id).filter(CartItem.Cart_id == cart.Cart_id).one()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in cart")
    
    item_price = session.query(Menu_items).filter(Menu_items.Item_id == item_id).one().Price

    session.delete(cart_item)
    session.commit()

    return {"message": f"Item {cart_item.Item_Name} removed from cart"}

@app.patch('/cart/update-item', tags=['cart'])
def update_item_in_cart(item: add_item_to_cart, user: Annotated[User, Depends(validate_role(roles=['customer','manager']))]):
    UID = user.UID
    cart = session.query(ShoppingCart).filter(ShoppingCart.UID == UID).filter(ShoppingCart.Status == 'Active').one()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    cart_item = session.query(CartItem).filter(CartItem.Item_id == item.Item_id).filter(CartItem.Cart_id == cart.Cart_id).one()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in cart")

    cart_item.Quantity = item.Quantity
    cart_item.Remarks = item.Remarks

    if cart_item.Quantity == 0:
        session.delete(cart_item)
        
    session.commit()

    return {"message": f"Item {cart_item.Item_Name} updated in cart"}

@app.patch('/cart/apply-voucher', tags=['cart'])
def apply_voucher_to_cart(voucher_code: int, user: Annotated[User, Depends(validate_role(roles=['customer','manager']))]):
    UID = user.UID
    cart = session.query(ShoppingCart).filter(ShoppingCart.UID == UID).filter(ShoppingCart.Status == 'Active').one()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    apply_voucher(voucher_code, UID, cart.Cart_id)
    return {"message": "Voucher applied successfully"}

@app.patch('/cart/remove-voucher', tags=['cart'])
def remove_voucher_from_cart(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))]):
    UID = user.UID
    cart = session.query(ShoppingCart).filter(ShoppingCart.UID == UID).filter(ShoppingCart.Status == 'Active').one()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    cart.VoucherApplied = None
    cart.Subtotal = calculate_subtotal(cart.Cart_id)
    cart.NetTotal = calculate_net_total(cart.Cart_id)
    session.commit()

    return {"message": "Voucher removed from cart"}

@app.get('/cart/view', tags=['cart'])
def view_cart(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))]):
    UID = user.UID
    cart = session.query(ShoppingCart).filter(ShoppingCart.UID == UID).filter(ShoppingCart.Status == 'Active').one()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    cart_items = session.query(CartItem).filter(CartItem.Cart_id == cart.Cart_id).all()
    items = [{"item_name": item.Item_Name, "quantity": item.Quantity} for item in cart_items]

    Subtotal = calculate_subtotal(cart.Cart_id)
    NetTotal = calculate_net_total(cart.Cart_id)

    return {
        "table_number": cart.Table_id,
        "cart_id": cart.Cart_id,
        "items": items,
        "voucher_applied": cart.VoucherApplied,
        "subtotal": Subtotal,
        "service_charge": cart.ServiceCharge,
        "service_tax": cart.ServiceTax,
        "rounding_adjustment": cart.RoundingAdjustment,
        "net_total": NetTotal,
        "status": cart.Status,
    }


@app.patch('/cart/submit', tags=['cart'])
def submit_cart(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))]):
    UID = user.UID
    cart = session.query(ShoppingCart).filter(ShoppingCart.UID == UID).filter(ShoppingCart.Status == 'Active').one()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    cart_items = session.query(CartItem).filter(CartItem.Cart_id == cart.Cart_id).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    order = SubmitOrder(order_created(UID=UID, Table_number=cart.Table_id, Subtotal=cart.Subtotal, ServiceCharge=cart.ServiceCharge, ServiceTax=cart.ServiceTax, RoundingAdjjustment=cart.RoundingAdjustment, NetTotal=cart.NetTotal), items_in_cart(items=[add_items_to_order(**item.model_dump()) for item in cart_items]))
    cart.Status = 'Submitted'
    session.commit()

@app.on_event("startup")
@repeat_every(seconds=60)  # Run every minute
def expire_old_carts():
    ten_minutes_ago = datetime.now() - timedelta(minutes=10)
    expired_carts = session.query(ShoppingCart).filter(
        ShoppingCart.LastUpdate < ten_minutes_ago,
        ShoppingCart.Status == 'Active'
    ).all()

    for cart in expired_carts:
        cart.Status = 'Expired'
        session.commit()

@app.get('/orders/view/{order_id}', response_model= order_created, tags=['orders'])
def view_order_details(order_id: int, user: Annotated[User, Depends(validate_role(roles=['Manager', 'Chef']))]):
    order = session.query(Order).filter(
        Order.UID == user.UID, func.date(Order.Time_Placed) == datetime.now().date()).order_by(Order.Time_Placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_items = session.query(OrderItem).filter_by(Order_ID=order.Order_id).all()
    items = [{"item_name": item.Item_Name, "quantity": item.Quantity, "remarks" : item.Remarks,"status": item.Status} for item in order_items]

    customer = session.query(User).filter_by(UID=order.UID).one()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    return {
        "table_number": order.Table_number,
        "order_id": order.Order_id,
        "customer_name": customer.Username,
        "order_items": items,
        "time_placed": order.Time_Placed,
        "voucher_applied": order.VoucherApplied,
        "Subtotal": order.Subtotal,
        "ServiceCharge": order.ServiceCharge,
        "ServiceTax": order.ServiceTax,
        "RoundingAdjustment": order.RoundingAdjustment,
        "NetTotal": order.NetTotal,
        "paying_method": 'Not Paid Yet'
    }

@app.patch('orders/cancel_item', tags=['orders'])
def cancel_order_item(user: Annotated[User, Depends(validate_role(roles=['customer', 'manager']))], Item_id: int):
    order = session.query(Order).filter(
        Order.UID == user.UID, func.date(Order.Time_Placed) == datetime.now().date()).order_by(Order.Time_Placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_item = session.query(OrderItem).filter(OrderItem.Order_id == order.Order_id, OrderItem.Item_id == Item_id).one()
    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in order")

    if order_item.Status != 'Order Received':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only items with status 'Order Received' can be cancelled")

    order_item.Status = 'Cancelled'
    order.Subtotal -= order_item.Quantity * session.query(Menu_items).filter(Menu_items.Item_id == Item_id).one().Price
    apply_voucher(order.VoucherApplied, order.UID, order.Order_id)
    order.ServiceCharge = order.Subtotal * 0.06
    order.ServiceTax = order.Subtotal * 0.06
    order.NetTotal = order.Subtotal + order.ServiceCharge + order.ServiceTax
    net_total_str = f"{order.NetTotal:.2f}"
    second_decimal = int(net_total_str[-1])
    if second_decimal in {1, 2, 3, 4}:
        order.NetTotal = round(order.NetTotal, 1) + 0.05
    elif second_decimal in {6, 7, 8, 9}:
        order.NetTotal = round(order.NetTotal, 1) + 0.10

    order.NetTotal = round(order.NetTotal, 2)
    order.RoundingAdjustment = order.NetTotal - (order.Subtotal + order.ServiceCharge + order.ServiceTax)

    session.commit()

    return {"message": "Item cancelled"}

@app.patch('/orders/update-status', tags=['orders'])
def update_order_status(user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))],Order_id: int, Item_id: int,new_status: Literal['Order Received','In Progress','Served','Cancelled']):
    order = session.query(Order).filter(Order.Order_id == Order_id).one()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_item = session.query(OrderItem).filter(OrderItem.Order_id == Order_id, OrderItem.Item_id == Item_id).one()
    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in order")

    order_item.Status = new_status
    session.commit()

    return {"message": f"Order status updated to {new_status}"}

@app.get('/orders/history', tags=['orders'])
def get_order_history(user: Annotated[User, Depends(validate_role(roles=['customer', 'manager']))]):
    orders = session.query(Order).filter(Order.UID == user.UID).order_by(Order.Time_Placed.desc()).all()
    order_list = []

    for order in orders:
        order_items = session.query(OrderItem).filter(OrderItem.Order_id == order.Order_id).all()
        items = [{"item_name": item.Item_Name, "quantity": item.Quantity, "remarks" : item.Remarks,"status": item.Status} for item in order_items]

        order_list.append({
            "table_number": order.Table_number,
            "order_id": order.Order_id,
            "order_items": items,
            "time_placed": order.Time_Placed,
            "voucher_applied": order.VoucherApplied,
            "Subtotal": order.Subtotal,
            "ServiceCharge": order.ServiceCharge,
            "ServiceTax": order.ServiceTax,
            "RoundingAdjustment": order.RoundingAdjustment,
            "NetTotal": order.NetTotal,
            "paying_method": order.PayingMethod
        })

    return order_list


@app.get('/orders/view_order_items', tags=['orders'])
def get_order_items_by_status(user: Annotated[User, Depends(validate_role(roles=['customer', 'manager']))], status: Optional[Literal['Order Received', 'In Progress', 'Served', 'Cancelled']] = None):
    query = session.query(OrderItem)
    if status:
        query = query.filter(OrderItem.Status == status)
    order_items = query.all()
    items = [{"item_name": item.Item_Name, "quantity": item.Quantity, "remarks": item.Remarks} for item in order_items]

    return items

