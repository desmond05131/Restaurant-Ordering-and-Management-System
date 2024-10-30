from pydantic import BaseModel, Field
from datetime import datetime,date, timezone, time
from fastapi import Depends, HTTPException, status, Query
from typing import Annotated,Literal,List, Optional
from sqlalchemy import select, and_, func

from root.account.get_user_data_from_db import get_role
from root.components.inventory_management import item, inventory
from root.account.account import validate_role
from root.database.database_models import User,VoucherRequirement, Inventory, Order, OrderItem, session, MenuItem, ItemIngredient, CartItem, ShoppingCart, Voucher
from root.database.data_format import voucher_base, voucher_requirement_base, UserVoucher
from api import app


def create_voucher(voucher: voucher_base, voucher_requirement: voucher_requirement_base):
    new_voucher = Voucher(
        voucher_code = voucher.voucher_code,
        voucher_type = voucher.voucher_type,
        description = voucher.description,
        discount_value = voucher.discount_value,
        expiry_date = voucher.expiry_date,
        begin_date = voucher.begin_date,
        required_points = voucher.required_points,
        usage_limit = voucher.usage_limit
    )
    session.add(new_voucher)
    session.flush([new_voucher])
   
    new_voucher_requirement = VoucherRequirement(
        voucher_id = new_voucher.voucher_id,
        applicable_item_id = voucher_requirement.applicable_item_id,
        requirement_time = voucher_requirement.requirement_time,
        minimum_spend = voucher_requirement.minimum_spend,
        capped_amount = voucher_requirement.capped_amount
    )
    
    session.add(new_voucher_requirement)
    session.commit()
    return new_voucher
    
   
def claim_voucher(voucher_id: int, user_id: int):
    voucher = session.query(Voucher).filter(Voucher.voucher_id == voucher_id).first()
    if voucher is None:
        raise HTTPException(status_code=404, detail="Voucher not found")
    user = session.query(User).filter(User.user_id == user_id).first()
    new_user_voucher = UserVoucher(
        user_id = user_id,
        voucher_id = voucher_id
    )
    session.add(new_user_voucher)
    session.commit()
    print(f"User {user.username} has successfully claimed voucher {voucher.voucher_code}")


def redeem_voucher(voucher_id: int, user_id: int):
    voucher = session.query(Voucher).filter(Voucher.voucher_id == voucher_id).first()
    if voucher is None:
        raise HTTPException(status_code=404, detail="Voucher not found")
    user = session.query(User).filter(User.user_id == user_id).first()
    if user.points < voucher.required_points:
        raise HTTPException(status_code=400, detail="User does not have enough points")
    user.points -= voucher.required_points
    new_user_voucher = UserVoucher(
        user_id = user_id,
        voucher_id = voucher_id
    )
    session.add(new_user_voucher)
    session.commit()
    print(f"User {user.username} has successfully redeemed voucher {voucher.voucher_code}")



def apply_voucher(voucher_code: int, user_id: int, order_id: int):
    voucher = session.query(Voucher).filter(Voucher.voucher_code == voucher_code).first()
    if voucher is None:
        raise HTTPException(status_code=404, detail="Voucher not found")
    voucher_requirement = session.query(VoucherRequirement).filter(VoucherRequirement.voucher_id == voucher.voucher_id).first()
    user = session.query(User).filter(User.user_id == user_id).first()
    user_voucher = session.query(UserVoucher).filter(and_(UserVoucher.user_id == user_id, UserVoucher.voucher_id == voucher.voucher_id)).first()
    if user_voucher is None:
        raise HTTPException(status_code=400, detail="User has not claimed this voucher")
    cart = session.query(ShoppingCart).filter(ShoppingCart.user_id == user_id,func.date(ShoppingCart.creation_time) == datetime.now().date()).order_by(ShoppingCart.creation_time.desc()).first()
    if cart is None:    
        raise HTTPException(status_code=404, detail="Cart not found")
    if voucher.expiry_date < datetime.now().date():
        raise HTTPException(status_code=400, detail="Voucher has expired")
    if voucher.begin_date > datetime.now().date():
        raise HTTPException(status_code=400, detail="Voucher has not started yet")
    if voucher.usage_limit is not None:
        if voucher.usage_limit == 0:
            raise HTTPException(status_code=400, detail="Voucher has reached usage limit")
        else:
            voucher.usage_limit -= 1
    current_time = datetime.now().time()
    if voucher_requirement.requirement_time > current_time:
        raise HTTPException(status_code=400, detail="Voucher has not reached requirement time")
    if voucher_requirement.minimum_spend > cart.subtotal:
        raise HTTPException(status_code=400, detail="Minimum spend not reached")
    
    if voucher.voucher_type == 'percentage discount':
        discount = cart.subtotal * voucher.discount_value
        if voucher_requirement.capped_amount is not None:
            if discount > voucher_requirement.capped_amount:
                discount = voucher_requirement.capped_amount
        cart.subtotal -= discount

    elif voucher.voucher_type == 'fixed amount discount':
        discount = voucher.discount_value
        cart.subtotal -= discount


    elif voucher.voucher_type == 'free item':
        discount = 0
        new_order_item = OrderItem(
            order_id = order_id,
            item_id = voucher_requirement.applicable_item_id,
            quantity = 1,
            price = 0
        )
        session.add(new_order_item)

    cart.voucher_applied = voucher_code
    session.commit()
    print(f"User {user.username} has successfully applied voucher {voucher.voucher_code} to order {order_id}")
       

    
@app.post("/voucher/create",tags=["Voucher"])
def create_voucher_endpoint(voucher: voucher_base, voucher_requirement: voucher_requirement_base,user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))]):
    if session.query(Voucher).filter(Voucher.voucher_code == voucher.voucher_code).first() is not None:
        raise HTTPException(status_code=400, detail="Voucher code already exists")
    create_voucher(voucher, voucher_requirement)
    return {"message": "Voucher created successfully"}

@app.post("/voucher/claim",tags=["Voucher"])
def claim_voucher_endpoint(voucher_id: int, user_id: int,user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))]):
    claim_voucher(voucher_id, user_id)
    return {"message": "Voucher claimed successfully"}

@app.post("/voucher/redeem",tags=["Voucher"])
def redeem_voucher_endpoint(voucher_id: int, user_id: int,user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))]):
    redeem_voucher(voucher_id, user_id)
    return {"message": "Voucher redeemed successfully"}

@app.get('/voucher/view', tags=["Voucher"])
def view_voucher( user: Annotated[User, Depends(validate_role(roles=['cashier', 'manager']))],voucher_id: int, voucher_type: Optional[Literal['percentage discount', 'fixed amount discount', 'free item']] = None):
    query = session.query(UserVoucher).filter(UserVoucher.voucher_id == voucher_id)
    if voucher_type:
        query = query.join(Voucher).filter(Voucher.voucher_type == voucher_type)
    
    user_voucher = query.all()
    
    if not user_voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    return user_voucher
                                                       


