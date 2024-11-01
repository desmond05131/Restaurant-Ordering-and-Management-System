from fastapi import Depends, HTTPException, status
from typing import Annotated, Any, List, Dict, Optional

from root.account.account import validate_role
from root.database.database_models import session,User, ItemIngredient
from api import app
from root.schemas.item import ItemIngredientsInput



@app.post('/ingredients/add', tags = ['Ingredients'])
def add_ingredients( ingredient: ItemIngredientsInput, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    existing_ingredient = session.query(ItemIngredient).filter_by(item_id=ingredient.item_id, inventory_id = ingredient.inventory_id).first()
    if existing_ingredient:
        raise HTTPException(status_code=status.HTTP_201_CREATED,detail= "Ingredient for item already stored")

    ingredient = ItemIngredient(item_id=ingredient.item_id, inventory_id=ingredient.inventory_id,quantity = ingredient.quantity)
    session.add(ingredient)
    session.commit()
    return {"message": f"Ingredient '{ingredient.inventory.inventory_name}' added successfully"}

@app.patch('/ingredients/manage', tags=['Ingredients'])
def manage_ingredients(ingredient: ItemIngredientsInput, user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))]) -> Dict[str,str] :
    ingredient_update = session.query(ItemIngredient).filter_by(item_id=ingredient.item_id, inventory_id = ingredient.inventory_id).first()
    if not ingredient_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail= "Item not found")
    
    ingredient_update.item_id = ingredient.item_id 
    ingredient_update.inventory_id = ingredient.inventory_id 
    ingredient_update.quantity = ingredient.quantity 
   
    session.commit()
    return {"message": f"Ingredient '{ingredient_update.inventory.inventory_name}' updated successfully"}


@app.delete('/ingredients/remove', tags = ['Ingredients'])
def remove_ingredient (user: Annotated[User, Depends(validate_role(roles=['manager','chef']))],item_id: int, inventory_id : int):
    ingredient = session.query(ItemIngredient).filter_by(item_id=item_id,inventory_id = inventory_id ).first()

    if not ingredient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")

    session.delete(ingredient)
    session.commit()
    return {"message": f"Ingredient '{ingredient.inventory.inventory_name}' removed successfully"}

@app.get('/ingredients/view', tags=['Ingredients'])
def view_ingredients(user: Annotated[User, Depends(validate_role(roles=['manager', 'chef']))], item_id: Optional[int] = None) -> List[Dict[str, Any]]:
    if item_id:
        ingredients = session.query(ItemIngredient).filter(ItemIngredient.item_id==item_id).all()
    else:
        ingredients = session.query(ItemIngredient).all()
    return [{"Item_id": ingredient.item_id, "Inventory_id": ingredient.inventory_id, "Quantity": ingredient.quantity} for ingredient in ingredients]