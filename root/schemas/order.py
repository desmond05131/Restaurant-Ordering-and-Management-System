from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime

class OrderCreated(BaseModel):
    order_id: Optional[int] = Field(None, alias='order_id')
    user_id: int
    table_number: int
    time_placed: datetime
    voucher_applied: Optional[int] = Field(None, alias='voucher_applied')
    subtotal: float
    service_charge: float
    service_tax: float
    rounding_adjustment: float
    net_total: float
    paying_method: Optional[Literal['Not Paid Yet','Cash','Credit Card','Debit Card','E-Wallet']] = Field('Not Paid Yet', alias='PayingMethod')

class OrderItemDetails(BaseModel):
    order_id: Optional[int] = Field(None, alias='order_id')
    item_id: int
    item_name: str
    quantity: int
    remarks: Optional[str]
    status: Literal['Order Received','In Progress','Served','Cancelled']

class AddItemsToOrder(OrderItemDetails):
    pass

class ItemsOrdered(BaseModel):
    orders: List[AddItemsToOrder]

class OrderInput(OrderCreated):
    pass

class UpdateStatus(BaseModel):
    order_id: int
    new_status: str
