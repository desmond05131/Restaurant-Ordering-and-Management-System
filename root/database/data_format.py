from typing import Annotated, Optional, Literal, List, Dict
from pydantic import BaseModel, AfterValidator, Field
from datetime import datetime, date, time
from fastapi import Depends, HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound



class SignUpRequest(BaseModel):
    username: str
    email: str
    password: str

class EditUserRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

class Key(BaseModel):
    access_token: str
    token_type: str


class inventory(BaseModel):
    inventory_id : Optional[int] = Field(None, alias='Inventory_id')
    inventory_name : str
    quantity : Optional[float] = Field(None, alias='Quantity')
    unit: Optional[str]= None

class new_batch(BaseModel):
    batch_id: Optional[int] = Field(None, alias='Inventory_id')
    inventory_id: int
    no_of_package: int
    quantity_per_package: float
    acquisition_date: date
    expiration_date : date
    cost: float
    cost_per_unit : float

class batch_package(BaseModel):
    package_id: Optional[int] = Field(None, alias='Package_id')
    batch_id: int
    inventory_id: int
    status: Literal['New','In use','Finished']

class item(BaseModel):
    item_id : Optional[int] = Field(None, alias='Item_id')
    item_name : str
    price :  float
    picture_link : str
    description : str
    category : Literal['All','Brunch/Breakfast','Rice','Noodle','Italian','Main Courses','Sides','Signature Dishes','Vegan','Dessert','Beverages']


class ingredients_without_item_id(BaseModel):
    inventory_id: int
    quantity:float

class item_ingredients(BaseModel):
    item_id : int 
    inventory_id : int
    quantity : float

class add_new_batch(BaseModel):
    batch_id: Optional[int] = Field(None, alias='Inventory_id')
    inventory_id: int
    no_of_package: int
    quantity_per_package: float
    acquisition_date: date
    expiration_date : date
    cost: float
    cost_per_unit : float

class batch_package(BaseModel):
    package_id: Optional[int] = Field(None, alias='Package_id')
    batch_id: int
    inventory_id: int
    status: Literal['New','In use','Finished']

class inventory_update_request(BaseModel):
    inventory_name: str
    quantity: int
    unit: Optional[str]= None
  

class item_update_request(BaseModel):
    item_name : str
    price :  float
    picture_link : str
    description : str
    category : str

class new_item_with_ingredients(item_update_request):
    ingredients: List[ingredients_without_item_id]

class inventory_alert(BaseModel):
    inventory_name: str
    remain_quantity: float
    unit: str
    message: str

class voucher_base(BaseModel):
    voucher_id: Optional[int] = Field(None, alias='voucher_id')
    voucher_code: str
    voucher_type: Literal['percentage discount','fixed amount discount','free item']
    description: str
    discount_value: float
    expiry_date: date
    begin_date: date
    required_points: Optional[int] = Field(None, alias='required_points')
    usage_limit: Optional[int] = Field(None, alias='usage_limit')

class voucher_requirement_base(BaseModel):
    voucher_id: Optional[int] = Field(None, alias='voucher_id')
    applicable_item_id: Optional[int] = Field(None, alias='applicable_item_id')
    requirement_time: time
    minimum_spend: float
    capped_amount: Optional[float] = Field(None, alias='capped_amount')

class UserVoucher(BaseModel):
    user_id: int
    voucher_id: int
    used_date: Optional[date] = None


class shopping_cart(BaseModel):
    cart_id: Optional[int] = Field(None, alias='Cart_id')
    user_id: int
    table_number: int
    creation_time: datetime
    voucher_applied: Optional[int] = Field(None, alias='VoucherApplied')
    subtotal: float
    service_charge: float
    service_tax: float
    rounding_adjustment: float
    net_total : float
    status: Literal['Active','Expired','Submitted']
    last_update: datetime

class cart_item(BaseModel):
    item_id: int
    cart_id: int
    item_name: str
    quantity: int
    remarks: Optional[str]
    price: float = None
    added_time: datetime

class add_item_to_cart(cart_item):
    pass

class items_in_cart(BaseModel):
    items: List[add_item_to_cart]

class order_created(BaseModel):
    order_id: Optional[int] = Field(None, alias='Order_id')
    user_id: int
    table_number: int
    time_placed: datetime
    voucher_applied: Optional[int] = Field(None, alias='VoucherApplied')
    subtotal: float
    service_charge: float
    service_tax: float
    rounding_adjustment: float
    net_total : float
    paying_method: Optional[Literal['Not Paid Yet','Cash','Credit Card','Debit Card','E-Wallet']] = Field('Not Paid Yet', alias='PayingMethod')

class order_item_details(BaseModel):
    order_id: Optional[int] = Field(None, alias='Order_id')
    item_id: int
    item_name: str
    quantity: int
    remarks: Optional[str]
    status: Literal['Order Received','In Progress','Served','Cancelled']

class add_items_to_order(order_item_details):
    pass

class items_ordered(BaseModel):
    orders: List[add_items_to_order]

class Order(BaseModel):
    order_id: Optional[int] = Field(None, alias='Order_id')
    user_id: int
    table_number: int
    time_placed: datetime
    voucher_applied: Optional[int] = Field(None, alias='VoucherApplied')
    subtotal: float
    service_charge: float
    service_tax: float
    rounding_adjustment: float
    net_total : float
    paying_method: Optional[Literal['Not Paid Yet','Cash','Credit Card','Debit Card','E-Wallet']] = Field('Not Paid Yet', alias='PayingMethod')


class Get_item_ingredient(BaseModel):
    name: str
    quantity: float
    unit: str

class Get_item(item):
    ingredients: List[Get_item_ingredient] = None

class UpdateStatus(BaseModel):
    order_id: int
    new_status: str

