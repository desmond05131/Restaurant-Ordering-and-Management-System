from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date

class InventoryInput(BaseModel):
    inventory_id: Optional[int] = Field(None, alias='inventory_id')
    inventory_name: str
    quantity: Optional[float] = Field(None, alias='quantity')
    unit: Optional[str] = None

class NewBatch(BaseModel):
    batch_id: Optional[int] = Field(None, alias='inventory_id')
    inventory_id: int
    no_of_package: int
    quantity_per_package: float
    acquisition_date: date
    expiration_date: date
    cost: float
    cost_per_unit: float

class BatchPackageCreate(BaseModel):
    package_id: Optional[int] = Field(None, alias='package_id')
    batch_id: int
    inventory_id: int
    status: Literal['New','In use','Finished']

class InventoryUpdateRequest(BaseModel):
    inventory_name: str
    quantity: int
    unit: Optional[str] = None

class InventoryAlert(BaseModel):
    inventory_name: str
    remain_quantity: float
    unit: str
    message: str
