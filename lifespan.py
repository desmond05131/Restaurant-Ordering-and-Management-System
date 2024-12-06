from contextlib import asynccontextmanager

from root.components.inventory_management import recalculate_inventory_quantities, check_inventory_levels

@asynccontextmanager
def lifespan():
    recalculate_inventory_quantities()
    yield
    check_inventory_levels()
    print("Lifespan function called")
