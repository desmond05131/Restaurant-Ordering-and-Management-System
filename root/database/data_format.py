from typing import Annotated, Optional, Literal, List, Dict
from pydantic import BaseModel, AfterValidator, Field
from datetime import datetime, date
from fastapi import Depends, HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound



class SignUpRequest(BaseModel):
    Username: str
    Email: str
    Password: str

class EditUserRequest(BaseModel):
    Username: Optional[str] = None
    Email: Optional[str] = None
    Password: Optional[str] = None

class Key(BaseModel):
    access_token: str
    token_type: str


class inventory(BaseModel):
    Inventory_id : Optional[int] = Field(None, alias='Inventory_id')
    Inventory_name : str
    Quantity : Optional[float] = Field(None, alias='Quantity')
    Unit: Optional[str]= None

class new_batch(BaseModel):
    Batch_id: Optional[int] = Field(None, alias='Inventory_id')
    Inventory_id: int
    No_of_Package: int
    Quantity_per_package: float
    Acquisition_date: date
    Expiration_date : date
    Cost: float
    Cost_per_unit : float

class batch_package(BaseModel):
    Package_id: Optional[int] = Field(None, alias='Package_id')
    Batch_id: int
    Inventory_id: int
    Status: Literal['New','In use','Finished']

class item(BaseModel):
    Item_id : Optional[int] = Field(None, alias='Item_id')
    Item_name : str
    Price :  float
    Picture_link : str
    Description : str
    Category : Literal['All','Brunch/Breakfast','Rice','Noodle','Italian','Main Courses','Sides','Signature Dishes','Vegan','Dessert','Beverages']


class ingredients_without_item_id(BaseModel):
    Inventory_id: int
    quantity:float

class item_ingredients(BaseModel):
    Item_id : int 
    Inventory_id : int
    quantity : float

class add_new_batch(BaseModel):
    Batch_id: Optional[int] = Field(None, alias='Inventory_id')
    Inventory_id: int
    No_of_Package: int
    Quantity_per_package: float
    Acquisition_date: date
    Expiration_date : date
    Cost: float
    Cost_per_unit : float

class batch_package(BaseModel):
    Package_id: Optional[int] = Field(None, alias='Package_id')
    Batch_id: int
    Inventory_id: int
    Status: Literal['New','In use','Finished']

class inventory_update_request(BaseModel):
    inventory_name: str
    quantity: int
    unit: Optional[str]= None
  

class item_update_request(BaseModel):
    Item_name : str
    Price :  float
    Picture_link : str
    Description : str
    Category : str

class new_item_with_ingredients(item_update_request):
    Ingredients: List[ingredients_without_item_id]

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
    requirement_time: date
    minimum_spend: float
    capped_amount: Optional[float] = Field(None, alias='capped_amount')

class UserVoucher(BaseModel):
    UID: int
    voucher_id: int
    used_date: Optional[date] = None


class shopping_cart(BaseModel):
    Cart_id: Optional[int] = Field(None, alias='Cart_id')
    UID: int
    Table_number: int
    Creation_time: datetime
    VoucherApplied: Optional[int] = Field(None, alias='VoucherApplied')
    Subtotal: float
    ServiceCharge: float
    ServiceTax: float
    RoundingAdjustment: float
    NetTotal : float
    Status: Literal['Active','Expired','Submitted']
    LastUpdate: datetime

class cart_item(BaseModel):
    Item_id: int
    Cart_id: int
    Item_Name: str
    Quantity: int
    Remarks: Optional[str]
    Price: float = None
    Added_time: datetime

class add_item_to_cart(cart_item):
    pass

class items_in_cart(BaseModel):
    items: List[add_item_to_cart]

class order_created(BaseModel):
    Order_id: Optional[int] = Field(None, alias='Order_id')
    UID: int
    Table_number: int
    Time_Placed: datetime
    VoucherApplied: Optional[int] = Field(None, alias='VoucherApplied')
    Subtotal: float
    ServiceCharge: float
    ServiceTax: float
    RoundingAdjjustment: float
    NetTotal : float
    PayingMethod: Optional[Literal['Not Paid Yet','Cash','Credit Card','Debit Card','E-Wallet']] = Field('Not Paid Yet', alias='PayingMethod')

class order_item_details(BaseModel):
    Order_id: Optional[int] = Field(None, alias='Order_id')
    Item_id: int
    Item_name: str
    Quantity: int
    Remarks: Optional[str]
    Status: Literal['Order Received','In Progress','Served','Cancelled']

class add_items_to_order(order_item_details):
    pass

class items_ordered(BaseModel):
    orders: List[add_items_to_order]

class Order(BaseModel):
    Order_id: Optional[int] = Field(None, alias='Order_id')
    UID: int
    Table_number: int
    Time_Placed: datetime
    VoucherApplied: Optional[int] = Field(None, alias='VoucherApplied')
    Subtotal: float
    ServiceCharge: float
    ServiceTax: float
    RoundingAdjustment: float
    NetTotal : float
    PayingMethod: Optional[Literal['Not Paid Yet','Cash','Credit Card','Debit Card','E-Wallet']] = Field('Not Paid Yet', alias='PayingMethod')


class Get_item_ingredient(BaseModel):
    name: str
    quantity: float
    unit: str

class Get_item(item):
    Ingredients: List[Get_item_ingredient] = None

class UpdateStatus(BaseModel):
    Order_id: int
    New_status: str

