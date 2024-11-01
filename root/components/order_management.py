from datetime import datetime,timedelta
from fastapi import Depends, HTTPException, status
from fastapi_utils.tasks import repeat_every
from typing import Annotated,Literal,List, Optional
from sqlalchemy import and_, select, func

from root.components.voucher import apply_voucher, invalidate_used_voucher, unapply_voucher
from root.account.get_user_data_from_db import get_role
from root.account.account import validate_role
from root.database.database_models import User, Inventory, Order, OrderItem, UserVoucher, Voucher, VoucherRequirement, session,MenuItem,ItemIngredient, CartItem, ShoppingCart
from api import app
from root.schemas.cart import AddItemToCart, CartItemInput, ItemsInCart, ShoppingCartInput
from root.schemas.item import GetItem
from root.schemas.order import AddItemsToOrder, OrderCreated
from sqlalchemy.orm.exc import NoResultFound


def create_cart(cart_info: ShoppingCartInput):
    cart = session.query(ShoppingCart).filter(ShoppingCart.table_id == cart_info.table_number).filter(ShoppingCart.status == 'Active').one_or_none()
    if cart:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Table already has an active cart,please ask the waiter for assistance")
    
    # check if there is an active cart for the same user but different table
    existing_cart = session.query(ShoppingCart).filter(ShoppingCart.user_id == cart_info.user_id).filter(ShoppingCart.table_id != cart_info.table_number).filter(ShoppingCart.status == 'Active').one_or_none()
    if existing_cart:
        existing_cart.status = 'Expired'
   
    new_cart = ShoppingCart(
        user_id = cart_info.user_id,
        table_id = cart_info.table_number,
        creation_time = datetime.now(),
        subtotal = 0.0,
        service_charge = 0.0,
        service_tax = 0.0,
        rounding_adjustment = 0.0,
        net_total = 0.0,
        status = 'Active',
        last_update = datetime.now()
    )

    session.add(new_cart)
    session.commit()
    session.flush(new_cart)
    return new_cart

def cart_add_item(item: CartItem):
    cart_item = CartItem(
        item_id = item.item_id,
        cart_id = item.cart_id,
        item_name = item.item_name,
        quantity = item.quantity,
        remarks = item.remarks,
        price = item.price,
        added_time = datetime.now()
    )

    session.add(cart_item)
    session.commit()
    session.flush(cart_item)
    return cart_item

def calculate_subtotal(cart_id: int):
    cart = session.query(ShoppingCart).filter(ShoppingCart.cart_id == cart_id).one()
    cart_items = session.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    subtotal = 0.0
    for item in cart_items:
        subtotal += item.quantity * item.price

    cart.subtotal = subtotal
    session.commit()

    return cart.subtotal

def calculate_net_total(cart_id: int):
    cart = session.query(ShoppingCart).filter(ShoppingCart.cart_id == cart_id).one()
    cart.service_charge = cart.subtotal * 0.06
    cart.service_tax = cart.subtotal * 0.06
    cart.net_total = cart.subtotal + cart.service_charge + cart.service_tax
    net_total_str = f"{cart.net_total:.2f}"
    second_decimal = int(net_total_str[-1])
    if second_decimal in {1, 2, 3, 4}:
        cart.net_total = round(cart.net_total, 1) + 0.05
    elif second_decimal in {6, 7, 8, 9}:
        cart.net_total = round(cart.net_total, 1) + 0.10

    cart.net_total = round(cart.net_total, 2)
    cart.rounding_adjustment = cart.net_total - (cart.subtotal + cart.service_charge + cart.service_tax)
    session.commit()

    return cart.net_total

def recalculate_cart_totals(cart_id: int):
    """Recalculates all cart totals including voucher discounts"""
    cart = session.query(ShoppingCart).filter(ShoppingCart.cart_id == cart_id).one()
    
    # Calculate initial subtotal
    cart_items = session.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    subtotal = sum(item.quantity * item.price for item in cart_items)
    cart.subtotal = subtotal

    # Apply voucher if exists
    if cart.voucher_applied:
        voucher = session.query(Voucher).filter(Voucher.voucher_code == cart.voucher_applied).one()
        voucher_requirement = session.query(VoucherRequirement).filter(
            VoucherRequirement.voucher_id == voucher.voucher_id).one()

        if voucher.voucher_type == 'percentage discount':
            discount = cart.subtotal * voucher.discount_value
            if voucher_requirement.capped_amount is not None:
                discount = min(discount, voucher_requirement.capped_amount)
            cart.subtotal -= discount
        elif voucher.voucher_type == 'fixed amount discount':
            cart.subtotal -= voucher.discount_value

    # Calculate final totals
    cart.service_charge = cart.subtotal * 0.06
    cart.service_tax = cart.subtotal * 0.06
    cart.net_total = cart.subtotal + cart.service_charge + cart.service_tax

    # Apply rounding
    net_total_str = f"{cart.net_total:.2f}"
    second_decimal = int(net_total_str[-1])
    if second_decimal in {1, 2, 3, 4}:
        cart.net_total = round(cart.net_total, 1) + 0.05
    elif second_decimal in {6, 7, 8, 9}:
        cart.net_total = round(cart.net_total, 1) + 0.10

    cart.net_total = round(cart.net_total, 2)
    cart.rounding_adjustment = cart.net_total - (cart.subtotal + cart.service_charge + cart.service_tax)
    
    session.commit()
    return cart

def recalculate_order_totals(order_id: int):
    """Recalculates all order totals including voucher discounts"""
    order = session.query(Order).filter(Order.order_id == order_id).one()
    
    # Calculate initial subtotal
    order_items = session.query(OrderItem).filter(and_(OrderItem.order_id == order_id, OrderItem.status != 'Cancelled')).all()
    subtotal = sum(item.quantity * session.query(MenuItem).filter(MenuItem.item_id == item.item_id).one().price 
                  for item in order_items)
    order.subtotal = subtotal

    # Apply voucher if exists
    if order.user_voucher_id:
        user_voucher = session.query(UserVoucher).filter(UserVoucher.user_voucher_id == order.user_voucher_id).one()
        voucher = user_voucher.voucher
        voucher_requirement = session.query(VoucherRequirement).filter(
            VoucherRequirement.voucher_id == voucher.voucher_id).one()

        if voucher.voucher_type == 'percentage discount':
            discount = order.subtotal * voucher.discount_value
            if voucher_requirement.capped_amount is not None:
                discount = min(discount, voucher_requirement.capped_amount)
            order.subtotal -= discount
        elif voucher.voucher_type == 'fixed amount discount':
            order.subtotal -= voucher.discount_value

    # Calculate final totals  
    order.service_charge = order.subtotal * 0.06
    order.service_tax = order.subtotal * 0.06
    order.net_total = order.subtotal + order.service_charge + order.service_tax

    # Apply rounding
    net_total_str = f"{order.net_total:.2f}"
    second_decimal = int(net_total_str[-1])
    if second_decimal in {1, 2, 3, 4}:
        order.net_total = round(order.net_total, 1) + 0.05
    elif second_decimal in {6, 7, 8, 9}:
        order.net_total = round(order.net_total, 1) + 0.10

    order.net_total = round(order.net_total, 2)
    order.rounding_adjustment = order.net_total - (order.subtotal + order.service_charge + order.service_tax)
    
    session.commit()
    return order

def SubmitOrder(order_info: OrderCreated, items: List[CartItem]):
    new_order = Order(
        user_id = order_info.user_id,
        table_id = order_info.table_id,
        cart_id = order_info.cart_id,
        time_placed = datetime.now(),
        user_voucher_id = order_info.user_voucher_id,
        subtotal = order_info.subtotal,
        service_charge = order_info.service_charge,
        service_tax = order_info.service_tax,
        rounding_adjustment = order_info.rounding_adjustment,
        net_total = order_info.net_total,
        paying_method = 'Not Paid Yet'
    )

    session.add(new_order)
    session.commit()
    session.flush(new_order)

    for item in items:
        order_item = OrderItem(
            order_id = new_order.order_id,
            item_id = item.item_id,
            item_name = item.item_name,
            quantity = item.quantity,
            remarks = item.remarks,
            status = 'Order Received'
        )

        session.add(order_item)
        session.commit()

    return new_order.order_id


def get_order(order_id: int):
    return session.query(Order).filter(Order.order_id ==order_id).one()

def delete_all_order():
    session.query(Order).delete()
    session.query(OrderItem).delete()
    session.commit()


@app.get('/menu/view', tags=['Menu'])
async def view_menu_items(user: Annotated[User, Depends(validate_role(roles=['manager', 'chef', 'cashier', 'customer']))], search_keyword: str = None) -> List[GetItem]:

    if get_role(user.user_id) in ['manager', 'chef']:
        if search_keyword:
            search_keyword = f"%{search_keyword}%"
            query = session.query(MenuItem).where(
                and_(
                    MenuItem.is_deleted == False,
                    MenuItem.item_name.ilike(search_keyword) |
                    MenuItem.description.ilike(search_keyword) |
                    MenuItem.category.ilike(search_keyword)
                )
            )
        else:
            query = session.query(MenuItem).where(MenuItem.is_deleted == False)
        
        items = []

        for row in query.all():

            row_dict = {}
            row_dict["ingredients"] = []

            row_dict["item_id"] = row.item_id
            row_dict["item_name"] = row.item_name
            row_dict["price"] = row.price
            row_dict["description"] = row.description
            row_dict["category"] = row.category
            row_dict["picture_link"] = row.picture_link

            for inventory in session.execute(
                    select(
                        ItemIngredient.inventory_id, ItemIngredient.quantity
                    ).where(
                        row.item_id == ItemIngredient.item_id
                    )).all():

                ingredient_row = session.execute(
                    select(
                        Inventory.inventory_name,
                        Inventory.unit
                    ).where(
                        Inventory.inventory_id == inventory.inventory_id
                    )).one()

                row_dict["ingredients"].append({
                    "name": ingredient_row.inventory_name,
                    "unit": ingredient_row.unit,
                    "quantity": inventory.quantity
                })

            items.append(GetItem(**row_dict))

        return items
    else:
        items = []

        for item in session.query(MenuItem).where(MenuItem.is_deleted == False).order_by(MenuItem.item_id).all():
            items.append(GetItem(
                item_id = item.item_id,
                item_name = item.item_name,
                price = item.price,
                description = item.description,
                category = item.category,
                picture_link = item.picture_link
            ))

        return items

@app.patch('/cart/add_item', tags=['Cart'])
def add_items_to_cart(item: AddItemToCart,table_number: int, user: Annotated[User, Depends(validate_role(roles=['customer','manager']))]):
    user_id = user.user_id
    
    order = session.query(Order).filter(and_(Order.table_id == table_number, Order.paying_method == 'Not Paid Yet', Order.is_cancelled == False)).one_or_none()
    if order:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Table is currently occupied")
    
    try:
        cart = session.query(ShoppingCart).filter(ShoppingCart.user_id == user_id).filter(ShoppingCart.table_id == table_number).filter(ShoppingCart.status == 'Active').one()
        if not cart:
            raise NoResultFound
    except NoResultFound:
        cart = create_cart(ShoppingCartInput(user_id=user_id, table_number=table_number, status='Active'))

    try:
        menu_item = session.query(MenuItem).filter(MenuItem.item_id == item.item_id).one()
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    
    if any(cart_item.item_id == item.item_id for cart_item in cart.cart_items):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Item {menu_item.item_name} already in cart")
    
    item_data = item.model_dump()
    item_data.update({
        'cart_id': cart.cart_id,
        'price': menu_item.price,
        'item_name': menu_item.item_name
    })
    cart_item = cart_add_item(CartItem(**item_data))

    session.commit()
    
    return {"message": f"Item {cart_item.item_name} added to cart"}

@app.patch('/cart/remove_item', tags=['Cart'])
def remove_item_from_cart(item_id: int, user: Annotated[User, Depends(validate_role(roles=['customer','manager']))]):
    user_id = user.user_id
    try:
        cart = session.query(ShoppingCart).filter(ShoppingCart.user_id == user_id).filter(ShoppingCart.status == 'Active').one()
        if not cart:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    
    try:
        cart_item = session.query(CartItem).filter(CartItem.item_id == item_id).filter(CartItem.cart_id == cart.cart_id).one()
        if not cart_item:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in cart")

    session.delete(cart_item)
    session.commit()

    return {"message": f"Item {cart_item.item_name} removed from cart"}

@app.patch('/cart/update_item', tags=['Cart'])
def update_item_in_cart(item: AddItemToCart, user: Annotated[User, Depends(validate_role(roles=['customer','manager']))]):
    user_id = user.user_id
    try:
        cart = session.query(ShoppingCart).filter(ShoppingCart.user_id == user_id).filter(ShoppingCart.status == 'Active').one()
        if not cart:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    try:
        cart_item = session.query(CartItem).filter(CartItem.item_id == item.item_id).filter(CartItem.cart_id == cart.cart_id).one()
        if not cart_item:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in cart")

    cart_item.quantity = item.quantity
    cart_item.remarks = item.remarks

    if cart_item.quantity == 0:
        session.delete(cart_item)

    session.commit()
    
    return {"message": f"Item {cart_item.item_name} updated in cart"}

@app.patch('/cart/apply_voucher', tags=['Cart'])
def apply_voucher_to_cart(voucher_code: str, user: Annotated[User, Depends(validate_role(roles=['customer','manager']))]):
    user_id = user.user_id
    try:
        cart = session.query(ShoppingCart).filter(ShoppingCart.user_id == user_id).filter(ShoppingCart.status == 'Active').one()
        if not cart:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    recalculate_cart_totals(cart.cart_id)
    apply_voucher(voucher_code, user_id, cart.cart_id)
    return {"message": "Voucher applied successfully"}

@app.patch('/cart/remove_voucher', tags=['Cart'])
def remove_voucher_from_cart(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))]):
    user_id = user.user_id
    try:
        cart = session.query(ShoppingCart).filter(ShoppingCart.user_id == user_id).filter(ShoppingCart.status == 'Active').one()
        if not cart:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    unapply_voucher(cart.voucher_applied, user_id)

    cart.voucher_applied = None
    session.commit()

    return {"message": "Voucher removed from cart"}

@app.get('/cart/view', tags=['Cart'])
def view_cart(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))]):
    user_id = user.user_id
    try:
        cart = session.query(ShoppingCart).filter(ShoppingCart.user_id == user_id).filter(ShoppingCart.status == 'Active').one()
        if not cart:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    cart_items = session.query(CartItem).filter(CartItem.cart_id == cart.cart_id).all()
    items = [{"item_name": item.item_name, "quantity": item.quantity} for item in cart_items]

    # subtotal = calculate_subtotal(cart.cart_id)
    # net_total = calculate_net_total(cart.cart_id)
    
    recalculate_cart_totals(cart.cart_id)

    return {
        "table_number": cart.table_number,
        "cart_id": cart.cart_id,
        "items": items,
        "voucher_applied": cart.voucher_applied,
        "subtotal": cart.subtotal,
        "service_charge": cart.service_charge,
        "service_tax": cart.service_tax,
        "rounding_adjustment": cart.rounding_adjustment,
        "net_total": cart.net_total,
        "status": cart.status,
    }


@app.patch('/cart/submit', tags=['Cart'])
def submit_cart(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))]):
    user_id = user.user_id
    try:
        cart = session.query(ShoppingCart).filter(ShoppingCart.user_id == user_id).filter(ShoppingCart.status == 'Active').one()
        if not cart:
            raise NoResultFound
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    cart_items = session.query(CartItem).filter(CartItem.cart_id == cart.cart_id).all()
    if len(cart_items) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")
    
    recalculate_cart_totals(cart.cart_id)
    if cart.voucher_applied:
        user_voucher_id = invalidate_used_voucher(cart.voucher_applied, user_id)
    else:
        user_voucher_id = None

    SubmitOrder(OrderCreated(user_id=user_id, 
                             table_id=cart.table_number.table_id, 
                             cart_id=cart.cart_id,
                             subtotal=cart.subtotal, 
                             service_charge=cart.service_charge,
                             service_tax=cart.service_tax, 
                             rounding_adjustment=cart.rounding_adjustment, 
                             user_voucher_id=user_voucher_id,
                             time_placed=datetime.now(),
                             net_total=cart.net_total), 
                        cart_items)
    cart.status = 'Submitted'
    session.commit()

@app.on_event("startup")
@repeat_every(seconds=60)  # Run every minute
def expire_old_carts():
    ten_minutes_ago = datetime.now() - timedelta(minutes=10)
    expired_carts = session.query(ShoppingCart).filter(
        ShoppingCart.last_update < ten_minutes_ago,
        ShoppingCart.status == 'Active'
    ).all()

    for cart in expired_carts:
        cart.status = 'Expired'
        if cart.voucher_applied:
            voucher = session.query(Voucher).filter(Voucher.voucher_code == cart.voucher_applied).one()
            voucher.usage_limit += 1
        session.commit()

@app.get('/orders/view/{order_id}', tags=['Orders'])
def view_order_details(order_id: int, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef', 'customer']))]):
    if get_role(user.user_id) in ['customer']:
        order = session.query(Order).filter(and_(Order.user_id == user.user_id, Order.paying_method == 'Not Paid Yet', Order.is_cancelled == False)).order_by(Order.time_placed.desc()).one_or_none()
    else:
        order = session.query(Order).filter(Order.order_id == order_id).one_or_none()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_items = session.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
    items = [{"item_name": item.item_name, "quantity": item.quantity, "remarks" : item.remarks,"status": item.status} for item in order_items]

    customer = session.query(User).filter_by(user_id=order.user_id).one()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    return {
        "table_number": order.table_number,
        "order_id": order.order_id,
        "customer_name": customer.username,
        "order_items": items,
        "time_placed": order.time_placed,
        "voucher_applied": order.user_voucher.voucher.voucher_code if order.user_voucher else None,
        "subtotal": order.subtotal,
        "service_charge": order.service_charge,
        "service_tax": order.service_tax,
        "rounding_adjustment": order.rounding_adjustment,
        "net_total": order.net_total,
        "paying_method": 'Not Paid Yet'
    }

@app.patch('/orders/cancel_item', tags=['Orders'])
def cancel_order_item(item_id: int, user: Annotated[User, Depends(validate_role(roles=['customer', 'manager']))]):
    order = session.query(Order).filter(and_(Order.user_id == user.user_id, Order.time_placed is not None)).order_by(Order.time_placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_item = session.query(OrderItem).filter(OrderItem.order_id == order.order_id, OrderItem.item_id == item_id).one_or_none()
    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in order")

    if order_item.status != 'Order Received':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only items with status 'Order Received' can be cancelled")

    order_item.status = 'Cancelled'
    session.commit()
    
    if all(item.status == 'Cancelled' for item in order.order_items):
        order.is_cancelled = True

    recalculate_order_totals(order.order_id)
    session.commit()

    return {"message": "Item cancelled"}

@app.patch('/orders/cancel', tags=['Orders'])
def cancel_order(item_id: int, user: Annotated[User, Depends(validate_role(roles=['customer', 'manager']))]):
    order = session.query(Order).filter(and_(Order.user_id == user.user_id, Order.time_placed is not None)).order_by(Order.time_placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if any(item.status == 'Served' or item.status == 'In Progress' for item in order.order_items):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel order while some items are preparing or served")

    for order_item in order.order_items:
        order_item.status = 'Cancelled'
    
    order.is_cancelled = True
    session.commit()

    recalculate_order_totals(order.order_id)
    session.commit()

    return {"message": "Order cancelled"}

@app.patch('/orders/update_status', tags=['Orders'])
def update_order_status(user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))],order_id: int, item_id: int,new_status: Literal['Order Received','In Progress','Served','Cancelled']):
    order = session.query(Order).filter(Order.order_id == order_id).one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_item = session.query(OrderItem).filter(OrderItem.order_id == order_id, OrderItem.item_id == item_id).one_or_none()
    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in order")

    order_item.status = new_status
    session.commit()

    recalculate_order_totals(order.order_id)
    session.commit()

    return {"message": f"Order status updated to {new_status}"}

@app.get('/orders/history', tags=['Orders'])
def get_order_history(user: Annotated[User, Depends(validate_role(roles=['customer', 'manager']))]):
    orders = session.query(Order).filter(Order.user_id == user.user_id).order_by(Order.time_placed.desc()).all()
    order_list = []

    for order in orders:
        order_items = session.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
        items = [{"item_name": item.item_name, "quantity": item.quantity, "remarks" : item.remarks,"status": item.status} for item in order_items]

        order_list.append({
            "table_number": order.table_number,
            "order_id": order.order_id,
            "order_items": items,
            "time_placed": order.time_placed,
            "voucher_applied": order.user_voucher.voucher.voucher_code if order.user_voucher else None,
            "subtotal": order.subtotal,
            "service_charge": order.service_charge,
            "service_tax": order.service_tax,
            "rounding_adjustment": order.rounding_adjustment,
            "net_total": order.net_total,
            "paying_method": order.paying_method,
            "is_cancelled": order.is_cancelled
        })

    return order_list


@app.get('/orders/view_order_items', tags=['Orders'])
def get_order_items_by_status(user: Annotated[User, Depends(validate_role(roles=['customer', 'manager']))], status: Optional[Literal['Order Received', 'In Progress', 'Served', 'Cancelled']] = None):
    query = session.query(OrderItem)
    if status:
        query = query.filter(OrderItem.status == status)
    order_items = query.all()
    items = [{"item_name": item.item_name, "quantity": item.quantity, "remarks": item.remarks} for item in order_items]

    return items

