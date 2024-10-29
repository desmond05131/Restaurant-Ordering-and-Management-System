from pydantic import BaseModel, AfterValidator, Field
from datetime import datetime, date
from fastapi import Depends, HTTPException, status
from typing import Annotated, List, Dict,Literal
from sqlalchemy import and_,extract, func
from sqlalchemy.orm.exc import NoResultFound
from fastapi_utils.tasks import repeat_every

from root.account.account import validate_role
from root.database.data_format import *
from root.database.database_models import session,User, Inventory, Menu_items, Item_ingredients, InventoryBatch, BatchPackage
from typing import Optional
from api import app



def create_inventory(ingredient: inventory):
    db_inventory = Inventory(
        Inventory_name= ingredient.Inventory_name,
        Quantity=ingredient.Quantity,
        Unit=ingredient.Unit,
    )
    session.add(db_inventory)
    session.commit()
    session.refresh(db_inventory)
    print(f"Inventory {db_inventory.Inventory_name} created successfully.")
    return db_inventory

def create_item(item: item):
    new_item = Menu_items(
        Item_name=item.Item_name,
        Price=item.Price,
        Picture_link=item.Picture_link,
        Description=item.Description,
        Category=item.Category,
    )

    session.add(new_item)
    session.commit()
    session.flush(new_item)
    print(f"Item {new_item.Item_name} created successfully.")
    return new_item

def create_item_ingredient(item_ingredient: item_ingredients):
        db_ingredient = Item_ingredients(
        Item_id = item_ingredient.Item_id, 
        Inventory_id = item_ingredient.Inventory_id,
        quantity = item_ingredient.quantity,
        )

        session.add(db_ingredient)
        session.commit()
        session.refresh(db_ingredient)
        print(f"Ingredients {db_ingredient.Item_id} created successfully.")
        return db_ingredient

def create_batch(batch: new_batch):
    db_batch = InventoryBatch(
        Batch_id = batch.Batch_id,
        Inventory_id = batch.Inventory_id,
        No_of_Package = batch.No_of_Package,
        Quantity_per_package = batch.Quantity_per_package,
        Acquisition_date = batch.Acquisition_date,
        Expiration_date = batch.Expiration_date,
        Cost = batch.Cost,
        Cost_per_unit = batch.Cost_per_unit,
    )
    session.add(db_batch)
    session.commit()
    session.refresh(db_batch)
    print(f"Batch {db_batch.Batch_id} created successfully.")
    return db_batch
    
def create_package(package: batch_package):
    db_package = BatchPackage(
        Batch_id = package.Batch_id,
        Inventory_id = package.Inventory_id,
        Status = 'New',
    )
    session.add(db_package)
    session.commit()
    session.refresh(db_package)
    print(f"Package {db_package.Package_id} created successfully.")
    return db_package

def update_quantity(inventory_id: int, no_of_package: int, quantity_per_package: float):
    inventory = session.query(Inventory).filter_by(Inventory_id=inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found")
    
    inventory.Quantity += no_of_package * quantity_per_package
    session.commit()
    print(f"Inventory {inventory.Inventory_name} updated successfully with new quantity: {inventory.Quantity}")
    return inventory

def send_stock_alert_message_(inventory_name: str, remain_quantity: int, unit: str):
    message = f"Alert: Only{remain_quantity} {unit} of {inventory_name} is left"
    print(message)

def check_stock_levels(Inventory: Inventory):
    if Inventory.Quantity <= 15:
        send_stock_alert_message_(Inventory.Inventory_name,Inventory.Quantity)

@app.post('/inventory/add', tags=['inventory'])
def add_inventory( new_inventory_info: inventory_update_request, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    existing_inventory = session.query(Inventory).filter_by(Inventory_name=new_inventory_info.inventory_name).first()
    if existing_inventory:
        raise HTTPException(status_code=status.HTTP_201_CREATED,detail= "Inventory already exist")
    
    else:
        new_inventory = create_inventory(inventory(
            Inventory_name=new_inventory_info.inventory_name,
            Quantity=new_inventory_info.quantity,
            Unit=new_inventory_info.unit
        ))
        return {"message": f"Product '{new_inventory_info.inventory_name}' created with {new_inventory_info.quantity} {new_inventory_info.unit}"}
        

@app.patch('/inventory/manage/details', tags=['inventory'])
def manage_inventory_details( inventory_update: inventory, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    inventory = session.query(Inventory).filter_by(Inventory_id=inventory_update.Inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= "Inventory not found")
    
    inventory.Inventory_name = inventory_update.Inventory_name
    inventory.Unit = inventory_update.Unit
    session.commit()
    return {"message": f"Product '{inventory_update.Inventory_name}' updated with unit: {inventory_update.Unit}"}


@app.delete('/inventory/remove', tags=['inventory'])
def remove_inventory(user: Annotated[User, Depends(validate_role(roles=['manager','chef']))],inventory_id: int, inventory_name: str):
    inventory = session.query(Inventory).filter_by(Inventory_name=inventory_name, Inventory_id= inventory_id).one()

    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found")

    session.delete(inventory)
    session.commit()
    return {"message": f"Inventory '{inventory_name}' removed successfully"}


@app.post('/inventory/batch/add', tags=['inventory'])
def restock(batch: add_new_batch, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    existing_batch = session.query(InventoryBatch).filter_by(Batch_id=batch.Batch_id).first()
    if existing_batch:
        raise HTTPException(status_code=status.HTTP_201_CREATED,detail= "Batch already exist")
    else:
        new_batch = create_batch(batch)
        update_quantity(batch.Inventory_id, batch.No_of_Package, batch.Quantity_per_package)
        for _ in range(batch.No_of_Package):
            create_package(batch_package(
                Batch_id=new_batch.Batch_id,
                Inventory_id=new_batch.Inventory_id,
                Status='New'
            ))
        return {"message": f"Batch '{new_batch.Batch_id}' created successfully with {batch.No_of_Package} packages"}
    
@app.patch('/inventory/batch/manage', tags=['inventory'])
def manage_batch_details(batch: new_batch, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    batch_update = session.query(InventoryBatch).filter_by(Batch_id=batch.Batch_id).first()
    if not batch_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= "Batch not found")
    initial_no_of_package = batch_update.No_of_Package
    initial_quantity_per_package = batch_update.Quantity_per_package

    batch_update.Inventory_id = batch.Inventory_id
    batch_update.No_of_Package = batch.No_of_Package
    batch_update.Quantity_per_package = batch.Quantity_per_package
    batch_update.Acquisition_date = batch.Acquisition_date
    batch_update.Expiration_date = batch.Expiration_date
    batch_update.Cost = batch.Cost
    batch_update.Cost_per_unit = batch.Cost_per_unit

    initial_total_quantity = initial_no_of_package * initial_quantity_per_package
    new_total_quantity = batch.No_of_Package * batch.Quantity_per_package

    if initial_total_quantity > new_total_quantity:
        update_quantity(batch.Inventory_id, -1, initial_total_quantity - new_total_quantity)
    else:
        update_quantity(batch.Inventory_id, 1, new_total_quantity - initial_total_quantity)

    if initial_no_of_package < batch.No_of_Package:
        for _ in range(batch.No_of_Package - initial_no_of_package):
            create_package(batch_package(
                Batch_id=batch.Batch_id,
                Inventory_id=batch.Inventory_id,
                Status='New'
            ))
    elif initial_no_of_package > batch.No_of_Package:
        packages_to_remove = session.query(BatchPackage).filter_by(Batch_id=batch.Batch_id).limit(initial_no_of_package - batch.No_of_Package).all()
        for package in packages_to_remove:
            session.delete(package)

    session.commit()
    return {"message": f"Batch '{batch.Batch_id}' updated successfully"}

@app.delete('/inventory/batch/remove', tags=['inventory'])
def remove_batch(user: Annotated[User, Depends(validate_role(roles=['manager','chef']))], batch_id: int, inventory_id: int):
    batch = session.query(InventoryBatch).filter_by(Batch_id=batch_id, Inventory_id=inventory_id).one()

    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    initial_no_of_package = batch.No_of_Package
    initial_quantity_per_package = batch.Quantity_per_package

    session.delete(batch)
    session.commit()
    session.query(BatchPackage).filter_by(Batch_id=batch_id).delete()
    update_quantity(inventory_id, -1, initial_no_of_package * initial_quantity_per_package)
    
    return {"message": f"Batch '{batch_id}' removed successfully"}

@app.post('/inventory/batch/package/add', tags=['inventory'])
def add_package(package: batch_package, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    existing_package = session.query(BatchPackage).filter_by(Package_id=package.Package_id).first()
    if existing_package:
        raise HTTPException(status_code=status.HTTP_201_CREATED, detail="Package already exists")
    else:
        new_package = create_package(package)
        batch = session.query(InventoryBatch).filter_by(Batch_id=package.Batch_id, Inventory_id=package.Inventory_id).first()
        if batch:
            batch.No_of_Package += 1
            session.commit()
            update_quantity(package.Inventory_id, 1, batch.Quantity_per_package)
        
        return {"message": f"Package '{new_package.Package_id}' created successfully"}
    
@app.patch('/inventory/batch/package/manage', tags=['inventory'])
def manage_package_details(package: batch_package, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    package_update = session.query(BatchPackage).filter_by(Package_id=package.Package_id).first()
    if not package_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    
    initial_inventory_id = package_update.Inventory_id
    initial_quantity_per_package = session.query(InventoryBatch).filter_by(Batch_id=package_update.Batch_id,Inventory_id=package_update.Inventory_id).first().Quantity_per_package
    new_quantity_per_package = session.query(InventoryBatch).filter_by(Batch_id=package.Batch_id,Inventory_id=package.Inventory_id).first().Quantity_per_package
    
    package_update.Batch_id = package.Batch_id
    package_update.Inventory_id = package.Inventory_id
    package_update.Status = package.Status

    if initial_inventory_id != package.Inventory_id:
        update_quantity(initial_inventory_id, -1, initial_quantity_per_package)
        update_quantity(package.Inventory_id, 1, new_quantity_per_package)

    session.commit()
    return {"message": f"Package '{package.Package_id}' updated successfully"}

@app.delete('/inventory/batch/package/remove', tags=['inventory'])
def remove_package(user: Annotated[User, Depends(validate_role(roles=['manager','chef']))], package_id: int, batch_id: int):
    package = session.query(BatchPackage).filter_by(Package_id=package_id, Batch_id=batch_id).one()

    if not package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

    inventory_id = package.Inventory_id
    quantity_per_package = session.query(InventoryBatch).filter_by(Batch_id=batch_id).first().Quantity_per_package

    session.delete(package)
    session.commit()

    update_quantity(inventory_id, -1, quantity_per_package)

    return {"message": f"Package '{package_id}' removed successfully"}


@app.post('/menu/items/add', tags=['menu'])
def add_menu_item(item: new_item_with_ingredients, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str, str]:
    existing_item = session.query(Menu_items).filter_by(Item_name=item.Item_name).first()
    if existing_item:
        raise HTTPException(status_code=status.HTTP_201_CREATED, detail="Item already exists")

    new_item = create_item(item)

    for ingredient in item.Ingredients:
        check_ingredient_existence = session.query(Inventory).filter_by(Inventory_id=ingredient.Inventory_id).first()  # Assuming you're querying Inventory table

        if not check_ingredient_existence:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ingredient with ID {ingredient.Inventory_id} not found")

        existing_ingredient = session.query(Item_ingredients).filter_by(
            Item_id=new_item.Item_id,
            Inventory_id=ingredient.Inventory_id
        ).first()

        if existing_ingredient:
            continue

        create_item_ingredient(item_ingredients(
            Item_id=new_item.Item_id,
            Inventory_id=ingredient.Inventory_id,
            quantity=ingredient.quantity
        ))

    return {
        "message": f"Product '{item.Item_name}' created in category: {item.Category} with price:{item.Price}; Ingredients added successfully"
    }

@app.patch('/menu/items/manage_details', tags=['menu'])
def manage_item_details(item_update: item, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    item = session.query(Menu_items).filter_by(Item_id=item_update.Item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= "Item not found")
    
    item.Item_name = item_update.Item_name
    item.Price = item_update.Price
    item.Picture_link = item_update.Picture_link
    item.Description =item_update.Description
    item.Category = item_update.Category
    session.commit()
    return {"message": f"Product '{item_update.Item_id}' updated successfully"}

@app.delete('/menu/items/remove', tags=['menu'])
def remove_item(user: Annotated[User, Depends(validate_role(roles=['manager','chef']))],item_name: str,item_id: int):

    delete_ingredient = session.query(Item_ingredients).filter_by(Item_id=item_id).delete()
    if not delete_ingredient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")

    session.commit()

    item = session.query(Menu_items).filter_by(Item_id=item_id,Item_name=item_name).one()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    session.delete(item)
    session.commit()
   
    return {"message": f"Item '{item_name}' and ingredients for '{item_name}' removed successfully"}


@app.post('/ingredients/add', tags = ['ingredients'])
def add_ingredients( ingredient: item_ingredients, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    existing_ingredient = session.query(Item_ingredients).filter_by(Item_id=ingredient.Item_id, Inventory_id = ingredient.Inventory_id).first()
    if existing_ingredient:
        raise HTTPException(status_code=status.HTTP_201_CREATED,detail= "Ingredient for item already stored")

    ingredient = Item_ingredients(Item_id=ingredient.Item_id, Inventory_id=ingredient.Inventory_id,quantity = ingredient.quantity)
    session.add(ingredient)
    session.commit()
    return {"message": f"Ingredient added successfully"}

@app.patch('/ingredients/manage', tags=['ingredients'])
def manage_ingredients(ingredient: item_ingredients, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    ingredient_update = session.query(Item_ingredients).filter_by(Item_id=ingredient.Item_id, Inventory_id = ingredient.Inventory_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= "Item not found")
    
    ingredient_update.Item_id = ingredient.Item_id 
    ingredient_update.Inventory_id = ingredient.Inventory_id 
    ingredient_update.quantity = ingredient.quantity 
   
    session.commit()
    return {"message": f"Ingredient '{ingredient_update.Item_id}' updated successfully"}


@app.delete('/ingredients/remove', tags = ['ingredients'])
def remove_ingredient (user: Annotated[User, Depends(validate_role(roles=['manager','chef']))],item_id: int, inventory_id : int):
    ingredient = session.query(Item_ingredients).filter_by(Item_id=item_id,Inventory_id = inventory_id ).one()

    if not ingredient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")

    session.delete(ingredient)
    session.commit()
    return {"message": f"Ingredient removed successfully"}


@app.on_event("startup")
@repeat_every(seconds=86400)  # 24 hours
def recalculate_inventory_quantities() -> None:
        inventories = session.query(Inventory).all()
        for inventory in inventories:
            initial_total_quantity = inventory.Quantity

            total_unopened_inventory = 0
            batches = session.query(InventoryBatch).filter_by(Inventory_id=inventory.Inventory_id).all()
            for batch in batches:
                quantity_in_new_package = sum( ## quantity of inventory for a batch
                    session.query(BatchPackage)
                    .filter_by(Batch_id=batch.Batch_id, Inventory_id=batch.Inventory_id, Status='New')
                    .count() * batch.Quantity_per_package
                )
                total_unopened_inventory += quantity_in_new_package ## total inventory include every batch

                In_use_package_quantity = initial_total_quantity - total_unopened_inventory
                in_use_expiration_date = session.query(InventoryBatch.Expiration_date).join(BatchPackage).filter(
                    BatchPackage.Inventory_id == inventory.Inventory_id,
                    BatchPackage.Status == 'In Use'
                ).order_by(InventoryBatch.Expiration_date).first()

                total_fresh_inventory = 0
                fresh_batches = session.query(InventoryBatch).filter_by(Inventory_id=inventory.Inventory_id).all()
                for batch in fresh_batches:
                    if batch.Expiration_date >= date.today():
                        quantity_in_new_package = sum( ## quantity of inventory for a batch
                            session.query(BatchPackage)
                            .filter_by(Batch_id=batch.Batch_id, Inventory_id=batch.Inventory_id, Status='New')
                            .count() * batch.Quantity_per_package
                        )

                        total_fresh_inventory += quantity_in_new_package ## total inventory include every batch except the in use one
                        if in_use_expiration_date >= date.today():
                            inventory.Quantity = total_fresh_inventory + In_use_package_quantity
                            session.commit()
                        else:
                            inventory.Quantity = total_fresh_inventory
                            session.commit()

            
            print(f"Recalculated inventory {inventory.Inventory_name}: Initial Quantity = {initial_total_quantity}, Total New Inventory = {total_fresh_inventory}, Updated Quantity = {inventory.Quantity}")



@app.on_event("startup")
@repeat_every(seconds=3600) 
def check_inventory_levels() -> None:
    inventories = session.query(Inventory).all()
    for inventory in inventories:
        check_stock_levels(inventory)

@app.get('/inventory/view', tags=['inventory'])
def view_inventory(user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> List[Dict[str, str]]:
    inventories = session.query(Inventory).all()
    return [{"Inventory_id": inventory.Inventory_id, "Inventory_name": inventory.Inventory_name, "Quantity": inventory.Quantity, "Unit": inventory.Unit} for inventory in inventories]

@app.get('/inventory/batch/view', tags=['inventory'])
def view_batch(user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> List[Dict[str, str]]:
    batches = session.query(InventoryBatch).all()
    return [{"Batch_id": batch.Batch_id, "Inventory_id": batch.Inventory_id, "No_of_Package": batch.No_of_Package, "Quantity_per_package": batch.Quantity_per_package, "Acquisition_date": batch.Acquisition_date, "Expiration_date": batch.Expiration_date, "Cost": batch.Cost, "Cost_per_unit": batch.Cost_per_unit} for batch in batches]

@app.get('/inventory/batch/package/view', tags=['inventory'])
def view_package(user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> List[Dict[str, str]]:
    packages = session.query(BatchPackage).all()
    return [{"Package_id": package.Package_id, "Batch_id": package.Batch_id, "Inventory_id": package.Inventory_id, "Status": package.Status} for package in packages]

@app.get('/menu/items/view', tags=['menu'])
def view_menu_items(user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> List[Dict[str, str]]:
    items = session.query(Menu_items).all()
    return [{"Item_id": item.Item_id, "Item_name": item.Item_name, "Price": item.Price, "Picture_link": item.Picture_link, "Description": item.Description, "Category": item.Category} for item in items]

@app.get('/ingredients/view', tags=['ingredients'])
def view_ingredients(user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> List[Dict[str, str]]:
    ingredients = session.query(Item_ingredients).all()
    return [{"Item_id": ingredient.Item_id, "Inventory_id": ingredient.Inventory_id, "quantity": ingredient.quantity} for ingredient in ingredients]

@app.get('/inventory/view/low', tags=['inventory'])
def view_low_inventory(user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> List[Dict[str, str]]:
    low_inventory = session.query(Inventory).filter(Inventory.Quantity <= 15).all()
    return [{"Inventory_id": inventory.Inventory_id, "Inventory_name": inventory.Inventory_name, "Quantity": inventory.Quantity, "Unit": inventory.Unit} for inventory in low_inventory]





