from pydantic import BaseModel, Field
from datetime import datetime,date, timezone, time
from fastapi import Depends, HTTPException, status, Query
from typing import Annotated,Literal,List, Optional
from sqlalchemy import select, and_, func

from root.components.voucher import voucher_base, voucher_requirement_base, create_voucher,apply_voucher
from root.account.get_user_data_from_db import get_role
from root.components.inventory_management import item, inventory
from root.account.account import validate_role
from root.database.database_models import User, Inventory, Order,UserItemRating,UserOverallFeedback, OrderItem, session, Menu_items, Item_ingredients, CartItem, ShoppingCart, Voucher
from root.database.data_format import *
from api import app

def count_number_of_ratings(item_id):
    return session.query(UserItemRating).filter(UserItemRating.Item_id == item_id).count()


def update_rating(item_id, rating):
    item = session.query(Menu_items).filter(Menu_items.Item_id == item_id).one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    number_of_ratings = count_number_of_ratings(item_id)

    item.Ratings = (item.Ratings * number_of_ratings + rating) / (number_of_ratings + 1)
    session.commit()

@app.post('/rating/rate-item', tags=['ratings'])
def rate_order_item(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))], rating: int, description: str, item_id: int):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be between 1 and 5")

    order = session.query(Order).filter(Order.UID == user.UID).order_by(Order.Time_Placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_item = session.query(OrderItem).filter(OrderItem.Order_id == order.Order_id, OrderItem.Item_id == item_id).one_or_none()
    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in order")

    if order.PayingMethod == 'Not Paid Yet':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot rate items before checkout")

    existing_rating = session.query(UserItemRating).filter(UserItemRating.UID == user.UID, UserItemRating.Item_id == item_id, UserItemRating.Order_id == order.Order_id).one_or_none()
    if existing_rating:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already rated this item for this order")

    new_user_item_rating = UserItemRating(
        UID=user.UID,
        Item_id=item_id,
        Order_id=order.Order_id,
        Rating=rating,
        Description=description
    )

    update_rating(item_id, rating)

    session.add(new_user_item_rating)
    session.commit()

    return {"message": f"Item {order_item.Item_Name} rated with {rating} stars"}

@app.patch('/rating/update-rating', tags=['ratings'])
def update_order_item_rating(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))], rating: int, description: str, item_id: int):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be between 1 and 5")

    order = session.query(Order).filter(Order.UID == user.UID).order_by(Order.Time_Placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_item = session.query(OrderItem).filter(OrderItem.Order_id == order.Order_id, OrderItem.Item_id == item_id).one_or_none()
    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in order")

    if order.PayingMethod == 'Not Paid Yet':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot rate items before checkout")

    existing_rating = session.query(UserItemRating).filter(UserItemRating.UID == user.UID, UserItemRating.Item_id == item_id, UserItemRating.Order_id == order.Order_id).one_or_none()
    if not existing_rating:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You have not rated this item for this order")

    initial_rating = existing_rating.Rating
    existing_rating.Rating = rating
    existing_rating.Description = description
    item = session.query(Menu_items).filter(Menu_items.Item_id == item_id).one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    number_of_ratings = count_number_of_ratings(item_id)
    item.Ratings = (item.Ratings * number_of_ratings - initial_rating + rating) / number_of_ratings
    session.commit()

    return {"message": f"Item {order_item.Item_Name} rating updated to {rating} stars"}

@app.post('/rating/overall', tags=['ratings'])
def submit_overall_feedback(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))], rating: int, description: str):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be between 1 and 5")

    order = session.query(Order).filter(Order.UID == user.UID).order_by(Order.Time_Placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.PayingMethod == 'Not Paid Yet':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot rate items before checkout")

    existing_feedback = session.query(UserOverallFeedback).filter(UserOverallFeedback.UID == user.UID, UserOverallFeedback.Order_id == order.Order_id).one_or_none()
    if existing_feedback:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already submitted feedback for this order")

    new_user_overall_feedback = UserOverallFeedback(
        UID=user.UID,
        Order_id=order.Order_id,
        Rating=rating,
        Description=description
    )
    session.add(new_user_overall_feedback)
    session.commit()

    return {"message": "Overall feedback submitted"}

@app.patch('/rating/update-overall', tags=['ratings'])
def update_overall_feedback(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))], rating: int, description: str):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be between 1 and 5")

    order = session.query(Order).filter(Order.UID == user.UID).order_by(Order.Time_Placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.PayingMethod == 'Not Paid Yet':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot rate items before checkout")

    existing_feedback = session.query(UserOverallFeedback).filter(UserOverallFeedback.UID == user.UID, UserOverallFeedback.Order_id == order.Order_id).one_or_none()
    if not existing_feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You have not submitted feedback for this order")

    existing_feedback.Overall_Rating = rating
    existing_feedback.Description = description
    session.commit()

    return {"message": "Overall feedback updated"}

@app.get('/rating/view', tags=['ratings'])
def view_item_ratings(user: Annotated[User, Depends(validate_role(roles=['customer', 'manager']))], item_id: Optional[int] = None):
    query = session.query(UserItemRating)
    
    if item_id is not None:
        query = query.filter(UserItemRating.Item_id == item_id)
    
    ratings = query.all()
    
    if not ratings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No ratings found")
    
    return ratings

@app.get('/rating/view-overall', tags=['ratings'])
def view_overall_ratings(user: Annotated[User, Depends(validate_role(roles=['customer', 'manager']))]):
    query = session.query(UserOverallFeedback)
    ratings = query.all()
    
    if not ratings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No ratings found")
    
    return ratings