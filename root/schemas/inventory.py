from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date

class InventoryUpdateInput(BaseModel):
    inventory_id: int
    inventory_name: str
    # quantity: Optional[float] = Field(None, alias='quantity')
    unit: Optional[str] = None

class BatchCreateInput(BaseModel):
    inventory_id: int
    no_of_package: int
    quantity_per_package: float
    acquisition_date: date
    expiration_date: date
    cost: float
    cost_per_unit: float
    
class BatchUpdateInput(BaseModel):
    batch_id: int
    no_of_package: int
    quantity_per_package: float
    acquisition_date: date
    expiration_date: date
    cost: float
    cost_per_unit: float
    status: Literal['New','In use','Finished']
    

class InventoryCreateInput(BaseModel):
    inventory_name: str
    quantity: int
    unit: Optional[str] = None

class InventoryAlert(BaseModel):
    inventory_name: str
    remain_quantity: float
    unit: str
    message: str
