from datetime import date
from fastapi import Depends, HTTPException, status
from typing import Annotated, Any, List, Dict, Optional
from fastapi_utils.tasks import repeat_every
from sqlalchemy import and_

from root.account.account import validate_role
from root.database.database_models import session,User, Inventory, MenuItem, ItemIngredient, InventoryBatch
from api import app
from root.schemas.item import ItemInput, ItemIngredientsInput, NewItemWithIngredients
from root.schemas.inventory import BatchUpdateInput, InventoryUpdateInput, BatchCreateInput, InventoryCreateInput



def create_inventory(ingredient: InventoryCreateInput):
    db_inventory = Inventory(
        inventory_name= ingredient.inventory_name,
        quantity=ingredient.quantity,
        unit=ingredient.unit,
    )
    session.add(db_inventory)
    session.commit()
    session.refresh(db_inventory)
    print(f"Inventory {db_inventory.inventory_name} created successfully.")
    return db_inventory

def create_item(item: ItemInput):
    new_item = MenuItem(
        item_name=item.item_name,
        price=item.price,
        picture_link=item.picture_link,
        description=item.description,
        category=item.category,
    )

    session.add(new_item)
    session.commit()
    session.flush(new_item)
    print(f"Item {new_item.item_name} created successfully.")
    return new_item

def create_item_ingredient(item_ingredient: ItemIngredientsInput):
        db_ingredient = ItemIngredient(
        item_id = item_ingredient.item_id, 
        inventory_id = item_ingredient.inventory_id,
        quantity = item_ingredient.quantity,
        )

        session.add(db_ingredient)
        session.commit()
        session.refresh(db_ingredient)
        print(f"Ingredients {db_ingredient.item_id} created successfully.")
        return db_ingredient

def create_batch(batch: BatchCreateInput):
    db_batch = InventoryBatch(
        inventory_id = batch.inventory_id,
        no_of_package = batch.no_of_package,
        quantity_per_package = batch.quantity_per_package,
        acquisition_date = batch.acquisition_date,
        expiration_date = batch.expiration_date,
        cost = batch.cost,
        cost_per_unit = batch.cost_per_unit,
        status = 'New'
    )
    session.add(db_batch)
    session.commit()
    session.refresh(db_batch)
    print(f"Batch {db_batch.batch_id} created successfully.")
    return db_batch
    
def update_quantity(inventory_id: int, no_of_package: int, quantity_per_package: float):
    inventory = session.query(Inventory).filter_by(inventory_id=inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found")
    
    inventory.quantity += no_of_package * quantity_per_package
    session.commit()
    print(f"Inventory {inventory.inventory_name} updated successfully with new quantity: {inventory.quantity}")
    return inventory

def send_stock_alert_message(inventory_name: str, remain_quantity: int, unit: str):
    message = f"Alert: Only {remain_quantity} {unit} of {inventory_name} is left in the inventory"
    print(message)

def check_stock_levels(inventory: Inventory):
    if inventory.quantity <= 15:
        send_stock_alert_message(inventory.inventory_name,inventory.quantity, inventory.unit)

@app.post('/inventory/add', tags=['Inventory'])
def add_inventory( new_inventory_info: InventoryCreateInput, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    existing_inventory = session.query(Inventory).filter_by(inventory_name=new_inventory_info.inventory_name, is_deleted=False).first()
    if existing_inventory:
        raise HTTPException(status_code=status.HTTP_201_CREATED,detail= "Inventory with this name already exist")
    
    else:
        create_inventory(InventoryCreateInput(
            inventory_name=new_inventory_info.inventory_name,
            quantity=new_inventory_info.quantity,
            unit=new_inventory_info.unit
        ))
        return {"message": f"Product '{new_inventory_info.inventory_name}' created with {new_inventory_info.quantity} {new_inventory_info.unit}"}
        
@app.patch('/inventory/manage/details', tags=['Inventory'])
def manage_inventory_details(inventory_update: InventoryUpdateInput, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    inventory = session.query(Inventory).filter_by(inventory_id=inventory_update.inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= "Inventory not found")
    
    inventory.inventory_name = inventory_update.inventory_name
    inventory.unit = inventory_update.unit
    session.commit()
    return {"message": f"Product '{inventory_update.inventory_name}' updated with unit '{inventory_update.unit}'"}

@app.delete('/inventory/remove', tags=['Inventory'])
def remove_inventory(inventory_id: int, user: Annotated[User, Depends(validate_role(roles=['manager','chef']))]):
    inventory = session.query(Inventory).filter_by(inventory_id=inventory_id, is_deleted=False).first()

    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found")

    inventory.is_deleted = True
    session.commit()
    return {"message": f"Inventory '{inventory.inventory_name}' removed successfully"}

@app.get('/inventory/view', tags=['Inventory'])
def view_inventory(user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> List[Dict[str, Any]]:
    inventories = session.query(Inventory).filter_by(is_deleted=False).all()
    return [{"Inventory_id": inventory.inventory_id, "Inventory_name": inventory.inventory_name, "Quantity": inventory.quantity, "Unit": inventory.unit} for inventory in inventories]

@app.get('/inventory/view/low', tags=['Inventory'])
def view_low_inventory(user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> List[Dict[str, Any]]:
    low_inventory = session.query(Inventory).filter(and_(Inventory.quantity <= 15, Inventory.is_deleted==False)).all()
    return [{"Inventory_id": inventory.inventory_id, "Inventory_name": inventory.inventory_name, "Quantity": inventory.quantity, "Unit": inventory.unit} for inventory in low_inventory]



@app.post('/inventory/batch/add', tags=['Inventory'])
def restock(batch: BatchCreateInput, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    if batch.no_of_package <= 0 or batch.quantity_per_package <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid package or quantity. Are you serious?")
    
    inventory = session.query(Inventory).filter_by(inventory_id=batch.inventory_id).first()
    if not inventory or inventory.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found")
    
    new_batch = create_batch(batch)
    update_quantity(batch.inventory_id, batch.no_of_package, batch.quantity_per_package)
    return {"message": f"Batch '{new_batch.batch_id}' created successfully with {batch.no_of_package} packages"}
    
@app.patch('/inventory/batch/manage', tags=['Inventory'])
def manage_batch_details(batch: BatchUpdateInput, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    batch_update = session.query(InventoryBatch).filter_by(batch_id=batch.batch_id).first()
    if not batch_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= "Batch not found")
    initial_no_of_package = batch_update.no_of_package
    initial_quantity_per_package = batch_update.quantity_per_package

    batch_update.no_of_package = batch.no_of_package
    batch_update.quantity_per_package = batch.quantity_per_package
    batch_update.acquisition_date = batch.acquisition_date
    batch_update.expiration_date = batch.expiration_date
    batch_update.cost = batch.cost
    batch_update.cost_per_unit = batch.cost_per_unit

    initial_total_quantity = initial_no_of_package * initial_quantity_per_package
    new_total_quantity = batch.no_of_package * batch.quantity_per_package

    if initial_total_quantity > new_total_quantity:
        update_quantity(batch_update.inventory_id, -1, initial_total_quantity - new_total_quantity)
    else:
        update_quantity(batch_update.inventory_id, 1, new_total_quantity - initial_total_quantity)

    session.commit()
    return {"message": f"Batch '{batch.batch_id}' updated successfully"}

@app.delete('/inventory/batch/remove', tags=['Inventory'])
def remove_batch(batch_id: int, user: Annotated[User, Depends(validate_role(roles=['manager','chef']))]):
    batch = session.query(InventoryBatch).filter(InventoryBatch.batch_id==batch_id).first()

    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    initial_no_of_package = batch.no_of_package
    initial_quantity_per_package = batch.quantity_per_package

    session.delete(batch)
    session.commit()
    update_quantity(batch.inventory_id, -1, initial_no_of_package * initial_quantity_per_package)
    
    return {"message": f"Batch '{batch_id}' removed successfully"}

@app.get('/inventory/batch/view', tags=['Inventory'])
def view_batch(user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> List[Dict[str, Any]]:
    batches = session.query(InventoryBatch).all()
    return [{"Batch_id": batch.batch_id, "Inventory_id": batch.inventory_id, "No_of_Package": batch.no_of_package, "Quantity_per_package": batch.quantity_per_package, "Acquisition_date": batch.acquisition_date, "Expiration_date": batch.expiration_date, "Cost": batch.cost, "Cost_per_unit": batch.cost_per_unit} for batch in batches]


@app.post('/menu/items/add', tags=['Menu'])
def add_menu_item(item: NewItemWithIngredients, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str, str]:
    existing_item = session.query(MenuItem).filter_by(item_name=item.item_name).first()
    if existing_item:
        raise HTTPException(status_code=status.HTTP_201_CREATED, detail="Item already exists")

    new_item = create_item(item)

    for ingredient in item.ingredients:
        check_ingredient_existence = session.query(Inventory).filter_by(inventory_id=ingredient.inventory_id).first()  # Assuming you're querying Inventory table

        if not check_ingredient_existence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ingredient with ID {ingredient.inventory_id} not found")

        existing_ingredient = session.query(ItemIngredient).filter_by(
            item_id=new_item.item_id,
            inventory_id=ingredient.inventory_id
        ).first()

        if existing_ingredient:
            continue

        create_item_ingredient(ItemIngredientsInput(
            item_id=new_item.item_id,
            inventory_id=ingredient.inventory_id,
            quantity=ingredient.quantity
        ))

    return {
        "message": f"Product '{item.item_name}' created in category: {item.category} with price:{item.price}; Ingredients added successfully"
    }

@app.patch('/menu/items/manage_details', tags=['Menu'])
def manage_item_details(item_update: ItemInput, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    item = session.query(MenuItem).filter_by(item_id=item_update.item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= "Item not found")
    
    item.item_name = item_update.item_name
    item.price = item_update.price
    item.picture_link = item_update.picture_link
    item.description =item_update.description
    item.category = item_update.category
    item.is_deleted = item_update.is_deleted
    session.commit()
    return {"message": f"Product '{item_update.item_id}' updated successfully"}

@app.delete('/menu/items/remove', tags=['Menu'])
def remove_item(user: Annotated[User, Depends(validate_role(roles=['manager','chef']))],item_name: str,item_id: int):
    try:
        delete_ingredient = session.query(ItemIngredient).filter_by(item_id=item_id).delete()
        if not delete_ingredient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
    except:
        pass

    session.commit()

    item = session.query(MenuItem).filter(and_(MenuItem.item_id==item_id,MenuItem.item_name==item_name, MenuItem.is_deleted==False)).one()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    item.is_deleted = True
    session.commit()
   
    return {"message": f"Item '{item_name}' and ingredients for '{item_name}' removed successfully"}


@app.on_event("startup")
@repeat_every(seconds=86400)  # 24 hours
def recalculate_inventory_quantities() -> None:
    inventories = session.query(Inventory).all()
    for inventory in inventories:
        initial_total_quantity = inventory.quantity

        total_unopened_inventory = 0
        batches = session.query(InventoryBatch).filter_by(inventory_id=inventory.inventory_id).all()
        for batch in batches:
            if batch.status == 'New':
                total_unopened_inventory += batch.no_of_package * batch.quantity_per_package

        In_use_package_quantity = initial_total_quantity - total_unopened_inventory
        in_use_expiration_date = session.query(InventoryBatch.expiration_date).filter(
            InventoryBatch.inventory_id == inventory.inventory_id,
            InventoryBatch.status == 'In Use'
        ).order_by(InventoryBatch.expiration_date).first()

        total_fresh_inventory = 0
        fresh_batches = session.query(InventoryBatch).filter_by(inventory_id=inventory.inventory_id).all()
        for batch in fresh_batches:
            if batch.expiration_date >= date.today():
                if batch.status == 'New':
                    total_fresh_inventory += batch.no_of_package * batch.quantity_per_package

        if in_use_expiration_date >= date.today():
            inventory.quantity = total_fresh_inventory + In_use_package_quantity
        else:
            inventory.quantity = total_fresh_inventory
        
        session.commit()
        print(f"Recalculated inventory {inventory.inventory_name}: Initial Quantity = {initial_total_quantity}, Total New Inventory = {total_fresh_inventory}, Updated Quantity = {inventory.quantity}")

@app.on_event("startup")
@repeat_every(seconds=3600) 
def check_inventory_levels() -> None:
    inventories = session.query(Inventory).filter_by(is_deleted=False).all()
    for inventory in inventories:
        check_stock_levels(inventory)






