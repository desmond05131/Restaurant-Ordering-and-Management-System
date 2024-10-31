from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime

class ShoppingCartInput(BaseModel):
    cart_id: Optional[int] = Field(None, alias='cart_id')
    user_id: int
    table_number: int
    creation_time: datetime = Field(default_factory=datetime.now)
    voucher_applied: Optional[int] = Field(None, alias='voucher_applied')
    # subtotal: float
    # service_charge: float
    # service_tax: float
    # rounding_adjustment: float
    # net_total: float
    status: Literal['Active','Expired','Submitted']
    last_update: datetime = Field(default_factory=datetime.now)

class CartItemInput(BaseModel):
    item_id: int
    cart_id: int
    item_name: str
    quantity: int
    remarks: Optional[str]
    price: float = None
    added_time: datetime

class AddItemToCart(CartItemInput):
    pass

class ItemsInCart(BaseModel):
    items: List[AddItemToCart]
