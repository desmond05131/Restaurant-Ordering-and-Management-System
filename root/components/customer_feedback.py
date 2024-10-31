from fastapi import Depends, HTTPException, status
from typing import Annotated,Optional

from root.account.account import validate_role
from root.database.database_models import User, Order,UserItemRating,UserOverallFeedback, OrderItem, session, MenuItem
from root.database.data_format import *
from api import app

def count_number_of_ratings(item_id):
    return session.query(UserItemRating).filter(UserItemRating.item_id == item_id).count()


def update_rating(item_id, rating):
    item = session.query(MenuItem).filter(MenuItem.item_id == item_id).one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    number_of_ratings = count_number_of_ratings(item_id)

    item.ratings = (item.ratings * number_of_ratings + rating) / (number_of_ratings + 1)
    session.commit()

@app.post('/rating/rate-item', tags=['Ratings'])
def rate_order_item(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))], rating: int, description: str, item_id: int):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be between 1 and 5")

    order = session.query(Order).filter(Order.user_id == user.user_id).order_by(Order.time_placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_item = session.query(OrderItem).filter(OrderItem.order_id == order.order_id, OrderItem.item_id == item_id).one_or_none()
    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in order")

    if order.paying_method == 'Not Paid Yet':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot rate items before checkout")

    existing_rating = session.query(UserItemRating).filter(UserItemRating.user_id == user.user_id, UserItemRating.item_id == item_id, UserItemRating.order_id == order.order_id).one_or_none()
    if existing_rating:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already rated this item for this order")

    new_user_item_rating = UserItemRating(
        user_id=user.user_id,
        item_id=item_id,
        order_id=order.order_id,
        rating=rating,
        description=description
    )

    update_rating(item_id, rating)

    session.add(new_user_item_rating)
    session.commit()

    return {"message": f"Item {order_item.item_name} rated with {rating} stars"}

@app.patch('/rating/update-rating', tags=['Ratings'])
def update_order_item_rating(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))], rating: int, description: str, item_id: int):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be between 1 and 5")

    order = session.query(Order).filter(Order.user_id == user.user_id).order_by(Order.time_placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_item = session.query(OrderItem).filter(OrderItem.order_id == order.order_id, OrderItem.item_id == item_id).one_or_none()
    if not order_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in order")

    if order.paying_method == 'Not Paid Yet':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot rate items before checkout")

    existing_rating = session.query(UserItemRating).filter(UserItemRating.user_id == user.user_id, UserItemRating.item_id == item_id, UserItemRating.order_id == order.order_id).one_or_none()
    if not existing_rating:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You have not rated this item for this order")

    initial_rating = existing_rating.rating
    existing_rating.rating = rating
    existing_rating.description = description
    item = session.query(MenuItem).filter(MenuItem.item_id == item_id).one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    number_of_ratings = count_number_of_ratings(item_id)
    item.ratings = (item.ratings * number_of_ratings - initial_rating + rating) / number_of_ratings
    session.commit()

    return {"message": f"Item {order_item.item_name} rating updated to {rating} stars"}

@app.post('/rating/overall', tags=['Ratings'])
def submit_overall_feedback(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))], rating: int, description: str):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be between 1 and 5")

    order = session.query(Order).filter(Order.user_id == user.user_id).order_by(Order.time_placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.paying_method == 'Not Paid Yet':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot rate items before checkout")

    existing_feedback = session.query(UserOverallFeedback).filter(UserOverallFeedback.user_id == user.user_id, UserOverallFeedback.order_id == order.order_id).one_or_none()
    if existing_feedback:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already submitted feedback for this order")

    new_user_overall_feedback = UserOverallFeedback(
        user_id=user.user_id,
        order_id=order.order_id,
        rating=rating,
        description=description
    )
    session.add(new_user_overall_feedback)
    session.commit()

    return {"message": "Overall feedback submitted"}

@app.patch('/rating/update-overall', tags=['Ratings'])
def update_overall_feedback(user: Annotated[User, Depends(validate_role(roles=['customer','manager']))], rating: int, description: str):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be between 1 and 5")

    order = session.query(Order).filter(Order.user_id == user.user_id).order_by(Order.time_placed.desc()).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.paying_method == 'Not Paid Yet':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot rate items before checkout")

    existing_feedback = session.query(UserOverallFeedback).filter(UserOverallFeedback.user_id == user.user_id, UserOverallFeedback.order_id == order.order_id).one_or_none()
    if not existing_feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You have not submitted feedback for this order")

    existing_feedback.overall_rating = rating
    existing_feedback.description = description
    session.commit()

    return {"message": "Overall feedback updated"}

@app.get('/rating/view', tags=['Ratings'])
def view_item_ratings(user: Annotated[User, Depends(validate_role(roles=['customer', 'manager']))], item_id: Optional[int] = None):
    query = session.query(UserItemRating)
    
    if item_id is not None:
        query = query.filter(UserItemRating.item_id == item_id)
    
    ratings = query.all()
    
    if not ratings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No ratings found")
    
    return ratings

@app.get('/rating/view-overall', tags=['Ratings'])
def view_overall_ratings(user: Annotated[User, Depends(validate_role(roles=['customer', 'manager']))]):
    query = session.query(UserOverallFeedback)
    ratings = query.all()
    
    if not ratings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No ratings found")
    
    return ratings