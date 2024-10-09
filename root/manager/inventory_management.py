from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from typing import Annotated, List, Dict
from sqlalchemy.orm import Session
from root.account.account import validate_role
from root.database.database_models import session,User, Inventory, Menu_items
from api import app
from typing import Optional


class inventory(BaseModel):
    Inventory_id : int
    Inventory_name : str
    Quantity : float
    Unit: Optional[str]= None

class item(BaseModel):
    Item_id : int
    Item_name : str
    Price :  float
    Picture_link : str
    Description : str
    Category : str

class inventory_update_request(BaseModel):
    inventory_name: str
    quantity: int
    unit: Optional[str]= None

class inventory_alert(BaseModel):
    inventory_name: str
    remain_quantity: int
    unit: str
    message: str

def create_item(item: item, session):
    db_item = Menu_items(
        Item_name=item.Item_name,
        Price=item.Price,
        Picture_link=item.Picture_link,
        Description=item.Description,
        Category=item.Category,
    )

    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

def create_ingredient(ingredient: inventory, session):
    db_ingredient = Inventory(
        Inventory_name=ingredient.Inventory_name,
        Quantity=ingredient.Quantity,
        Unit=ingredient.Unit
    )
    session.add(db_ingredient)
    session.commit()
    session.refresh(db_ingredient)
    return db_ingredient

def get_item(Item_id: int):
    return session.query(Menu_items).filter(Menu_items.Item_id == Item_id).one()

def send_stock_alert_message_(inventory_name: str, remain_quantity: int, unit: str):
    message = f"Alert: Only{remain_quantity} {unit} of {inventory_name} is left"
    print(message)

def check_stock_levels(Inventory: Inventory):
    if Inventory.Quantity <= 10:
        send_stock_alert_message_(Inventory.Inventory_name,Inventory.Quantity)

@app.patch('/inventory/manage', tags=['inventory'])
def manage_inventory(user: Annotated[User, Depends(validate_role(roles=['Manager', 'Chef']))], inventory_update: inventory_update_request) -> Dict[str,str] :
    inventory = session.query(Inventory).filter_by(Inventory_name=inventory_update.inventory_name).first()  
    if not inventory:
        new_inventory = Inventory(Inventory_name=inventory_update.inventory_name, Quantity=inventory_update.quantity)
        session.add(new_inventory)
        session.commit()
        return {"message": f"Product '{inventory_update.inventory_name}' added with {inventory_update.quantity} units"}
    
    Existing_quantity = inventory.Quantity
    inventory.Quantity += inventory_update.quantity 
    session.commit()

    check_stock_levels(inventory, session) 

    if inventory_update.quantity > 0:
        return {"message": f"Added {inventory_update.quantity} units to {inventory_update.inventory_name}. Total: {inventory.Quantity}"}
    else:
        return {"message": f"Updated {inventory_update.inventory_name} from {Existing_quantity} to {inventory.Quantity} units"}
    


@app.delete('/inventory/remove', tags=['inventory'])
def remove_inventory(user: Annotated[User, Depends(validate_role(roles=['Manager','Chef']))],inventory_name: str):
    inventory = session.query(Inventory).filter_by(Inventory_name=inventory_name).one()

    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found")

    session.delete(inventory)
    session.commit()
    return {"message": f"Inventory '{inventory_name}' removed successfully"}

@app.patch('/menu/items/add', tags = ['menu'])
def add_item_to_menu(user: Annotated[User, Depends(validate_role(roles=['Manager','Chef']))],Item: item):
    create_item(item)


## to be done by chef
##customer place order, inventory = inventory - order.item.ingredients