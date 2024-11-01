from pydantic import BaseModel, Field
from typing import Optional, Literal, List

class ItemInput(BaseModel):
    item_id: Optional[int] = Field(None, alias='item_id')
    item_name: str
    price: float
    picture_link: str
    description: str
    category: Literal['All','Brunch/Breakfast','Rice','Noodle','Italian','Main Courses','Sides','Signature Dishes','Vegan','Dessert','Beverages']
    is_deleted: bool

class IngredientsWithoutItemId(BaseModel):
    inventory_id: int
    quantity: float

class ItemIngredientsInput(BaseModel):
    item_id: int 
    inventory_id: int
    quantity: float

class ItemUpdateRequest(BaseModel):
    item_name: str
    price: float
    picture_link: str
    description: str
    category: Literal['All','Brunch/Breakfast','Rice','Noodle','Italian','Main Courses','Sides','Signature Dishes','Vegan','Dessert','Beverages']

class NewItemWithIngredients(ItemUpdateRequest):
    ingredients: List[IngredientsWithoutItemId]

class GetItemIngredient(BaseModel):
    name: str
    quantity: float
    unit: str

class GetItem(ItemInput):
    ingredients: List[GetItemIngredient] = None
