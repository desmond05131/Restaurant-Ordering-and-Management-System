from pydantic import BaseModel, Field
from datetime import datetime,date, timezone, time
from fastapi import Depends, HTTPException, status, Query
from typing import Annotated,Literal,List, Optional
from sqlalchemy import select, and_, func

from root.components.voucher import voucher_base, voucher_requirement_base, create_voucher,apply_voucher
from root.account.get_user_data_from_db import get_role
from root.components.inventory_management import item, inventory
from root.account.account import validate_role
from root.database.database_models import User, Inventory,Machine, Order,UserItemRating,UserOverallFeedback, OrderItem, session, MenuItem, ItemIngredient, CartItem, ShoppingCart, Voucher
from root.database.data_format import *
from api import app



@app.post('/machines/add-machine', tags=['Machines'])
def add_machine(machine_name: str,machine_type: str, cost:float, user: Annotated[User, Depends(validate_role(roles=['manager','chef']))]):
    new_machine = Machine(
        machine_name = machine_name,
        machine_type = machine_type,
        cost = cost
        
    )
    session.add(new_machine)
    session.commit()
    print(f"Machine {machine_name} has been added to the inventory")
    return new_machine


@app.patch('/machines/edit-machine', tags=['Machines'])
def edit_machine(machine_id: str,machine_name: str,machine_type: str, cost:float, user: Annotated[User, Depends(validate_role(roles=['manager','chef']))]):
    machine_to_edit = session.query(Machine).filter(Machine.machine_id == machine_id).one_or_none()
    if not machine_to_edit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found")
    machine_to_edit.machine_name = machine_name
    machine_to_edit.machine_type = machine_type
    machine_to_edit.cost = cost
    session.commit()
    print(f"Machine {machine_name} has been edited")
    return machine_to_edit

@app.delete('/machines/delete-machine', tags=['Machines'])
def delete_machine(machine_id: str, user: Annotated[User, Depends(validate_role(roles=['manager','chef']))]):
    machine_to_delete = session.query(Machine).filter(Machine.machine_id == machine_id).one_or_none()
    if not machine_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found")
    session.delete(machine_to_delete)
    session.commit()
    print(f"Machine {machine_to_delete.machine_name} has been deleted")
    return machine_to_delete

@app.patch('/machines/report_issue', tags=['Machines'])
def report_issue(machine_id: str, issue_description: str, user: Annotated[User, Depends(validate_role(roles=['manager','chef']))]):
    machine = session.query(Machine).filter(Machine.machine_id == machine_id).one_or_none()
    if not machine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found")
    machine.machine_status = "Under maintenance"
    machine.maintenance_required = True
    machine.issue_description = issue_description
    session.commit()
    print(f"Machine {machine.machine_name} has been reported with issue: {issue_description}")
    return machine


@app.patch('/machines/resolve_issue', tags=['Machines'])
def resolve_issue(machine_id: str, user: Annotated[User, Depends(validate_role(roles=['manager','chef']))]):
    machine = session.query(Machine).filter(Machine.machine_id == machine_id).one_or_none()
    if not machine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found")
    machine.machine_status = "Available"
    machine.maintenance_required = False
    machine.issue_description = None
    machine.last_maintenance= datetime.now()
    session.commit()
    print(f"Machine {machine.machine_name} has been resolved")
    return machine

@app.get('/machines/get-all-machines', tags=['Machines'])
def get_all_machines(user: Annotated[User, Depends(validate_role(roles=['manager','chef']))]):
    machines = session.query(Machine).all()
    return machines


