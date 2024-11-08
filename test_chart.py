import matplotlib.pyplot as plt
from typing import Optional, Dict
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from typing import Annotated, Dict,Literal,Optional
from sqlalchemy import func, extract
from escpos import printer
import zpl


from root.account.account import validate_role
from root.database.database_models import User,Machine, InventoryBatch, Order, OrderItem, session, MenuItem
from root.components.generate_receipt import generate_receipt

from api import app


current_time = datetime.now()
formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
print(formatted_time)


# # Sample data access function as provided
# def generate_sales_report(
#     time_period: Literal["year", "month", "week", "day"],
#     start_time: datetime,
#     end_time: datetime
# ) -> Dict[str, Dict[str, float]]:
#     # Assume `session` and `Order` are defined elsewhere
#     query = session.query(Order.time_placed,
#         func.count(Order.order_id).label('number_of_sales'),
#         func.sum(Order.net_total).label('total_net_total')
#     ).filter(Order.time_placed >= start_time, Order.time_placed <= end_time)

#     if time_period == "year":
#         query = query.group_by(extract('year', Order.time_placed))
#     elif time_period == "month":
#         query = query.group_by(extract('year', Order.time_placed), extract('month', Order.time_placed))
#     elif time_period == "week":
#         query = query.group_by(extract('year', Order.time_placed), extract('week', Order.time_placed))
#     elif time_period == "day":
#         query = query.group_by(extract('year', Order.time_placed), extract('month', Order.time_placed), extract('day', Order.time_placed))

#     sales = query.all()
#     if not sales:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sales data found for the given timeframe")

#     report = {}
#     for sale in sales:
#         if time_period == "year":
#             report_key = f"{sale[0].year}"
#         elif time_period == "month":
#             report_key = f"{sale[0].year}-{sale[0].month:02d}"
#         elif time_period == "week":
#             report_key = f"{sale[0].year}-W{sale[0].isocalendar()[1]:02d}"
#         elif time_period == "day":
#             report_key = f"{sale[0].year}-{sale[0].month:02d}-{sale[0].day:02d}"

#         report_time_period, number_of_sales, total_net_total = sale[0], sale[1], sale[2]
#         report[report_key] = {
#             "time_period": report_time_period,
#             "number_of_sales": number_of_sales if number_of_sales is not None else 0,
#             "total_net_total": total_net_total if total_net_total is not None else 0
#         }

#     return report


# def plot_sales_report(
#     sales_report: Dict[str, Dict[str, float]],
#     time_period: Literal["year", "month", "week", "day"]
# ):
#     # Extract data for plotting
#     dates = list(sales_report.keys())
#     number_of_sales = [data["number_of_sales"] for data in sales_report.values()]
#     total_net_total = [data["total_net_total"] for data in sales_report.values()]

#     # Create a figure and axis
#     fig, ax1 = plt.subplots(figsize=(10, 6))

#     # Plot number of sales on the left y-axis
#     ax1.set_xlabel("Time Period")
#     ax1.set_ylabel("Number of Sales", color="skyblue")
#     ax1.bar(dates, number_of_sales, color="skyblue", label="Number of Sales")
#     ax1.set_ylim(ymin=0)
#     ax1.tick_params(axis="y", labelcolor="skyblue")
#     ax1.legend(loc="upper left")

#     # Create a second y-axis for total net total
#     ax2 = ax1.twinx()
#     ax2.set_ylabel("Total Net Total", color="orange")
#     ax2.plot(dates, total_net_total, color="orange", label="Total Net Total",marker='o')
#     ax2.set_ylim(ymin=0)
#     ax2.tick_params(axis="y", labelcolor="orange")
#     ax2.legend(loc="upper right")

#     # Format the x-axis based on the time period
#     plt.xticks(rotation=45, ha="right")
#     plt.title(f"Sales Report ({time_period.capitalize()})")

#     # Show the plot
#     plt.tight_layout()
#     plt.show()

# sales_report = generate_sales_report("day", datetime(2023, 1, 1), datetime(2024, 12, 31))

# # Plot the sales report
# plot_sales_report(sales_report, "day")


# def generate_inventory_cost_report(
#     time_period: Literal["year", "month", "week", "day"],
#     start_time: datetime,
#     end_time: datetime
# ) -> Dict[str, Dict[str, float]]:
#     # Assume `session` and `InventoryBatch` are defined elsewhere
#     query = session.query(InventoryBatch.acquisition_date,
#         func.count(InventoryBatch.batch_id).label('number_of_batches'),
#         func.sum(InventoryBatch.cost).label('total_cost')
#     ).filter(InventoryBatch.acquisition_date >= start_time, InventoryBatch.acquisition_date <= end_time)

#     if time_period == "year":
#         query = query.group_by(extract('year', InventoryBatch.acquisition_date))
#     elif time_period == "month":
#         query = query.group_by(extract('year', InventoryBatch.acquisition_date), extract('month', InventoryBatch.acquisition_date))
#     elif time_period == "week":
#         query = query.group_by(extract('year', InventoryBatch.acquisition_date), extract('week', InventoryBatch.acquisition_date))
#     elif time_period == "day":
#         query = query.group_by(extract('year', InventoryBatch.acquisition_date), extract('month', InventoryBatch.acquisition_date), extract('day', InventoryBatch.acquisition_date))

#     costs = query.all()
#     if not costs:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No inventory cost data found for the given timeframe")

#     report = {}
#     for cost in costs:
#         if time_period == "year":
#             report_key = f"{cost[0].year}"
#         elif time_period == "month":
#             report_key = f"{cost[0].year}-{cost[0].month:02d}"
#         elif time_period == "week":
#             report_key = f"{cost[0].year}-W{cost[0].isocalendar()[1]:02d}"
#         elif time_period == "day":
#             report_key = f"{cost[0].year}-{cost[0].month:02d}-{cost[0].day:02d}"

#         report_time_period,number_of_batches, total_cost = cost[0], cost[1], cost[2]
#         report[report_key] = {
#             "time_period": report_time_period,
#             "number_of_batches": number_of_batches if number_of_batches is not None else 0,
#             "total_cost": total_cost if total_cost is not None else 0
#         }

#     return report

# def plot_inventory_cost_report(inventory_report: Dict[str, Dict[str, float]],
#     time_period: Literal["year", "month", "week", "day"]
# ):
#     # Extract data for plotting
#     dates = list(inventory_report.keys())
#     number_of_sales = [data["number_of_batches"] for data in inventory_report.values()]
#     total_net_total = [data["total_cost"] for data in inventory_report.values()]

#     # Create a figure and axis
#     fig, ax1 = plt.subplots(figsize=(10, 6))

#     # Plot number of sales on the left y-axis
#     ax1.set_xlabel("Time Period")
#     ax1.set_ylabel("Number of Acquisitions", color="skyblue")
#     ax1.bar(dates, number_of_sales, color="skyblue", label="Number of Acquisitions")
#     ax1.set_ylim(ymin=0)
#     ax1.tick_params(axis="y", labelcolor="skyblue")
#     ax1.legend(loc="upper left")

#     # Create a second y-axis for total net total
#     ax2 = ax1.twinx()
#     ax2.set_ylabel("Total Cost", color="orange")
#     ax2.plot(dates, total_net_total, color="orange", label="Total Cost",marker='o')
#     ax2.set_ylim(ymin=0)
#     ax2.tick_params(axis="y", labelcolor="orange")
#     ax2.legend(loc="upper right")

#     # Format the x-axis based on the time period
#     plt.xticks(rotation=45, ha="right")
#     plt.title(f"Inventory Cost Report ({time_period.capitalize()})")

#     # Show the plot
#     plt.tight_layout()
#     plt.show()

# cost_report = generate_inventory_cost_report("week", datetime(2023, 1, 1), datetime(2024, 12, 31))
# plot_inventory_cost_report(cost_report, "week")



# def generate_machine_cost_report(time_period: Literal["year", "month", "week", "day"],
#     start_time: datetime,
#     end_time: datetime
# ) -> Dict[str, Dict[str, float]]:
#     # Assume `session` and `InventoryBatch` are defined elsewhere
#     query = session.query(Machine.acquisition_date,
#         func.count(Machine.machine_id).label('number_of_machine_acquisition'),
#         func.sum(Machine.cost).label('total_cost')
#     ).filter(Machine.acquisition_date >= start_time, Machine.acquisition_date <= end_time)

#     if time_period == "year":
#         query = query.group_by(extract('year', Machine.acquisition_date))
#     elif time_period == "month":
#         query = query.group_by(extract('year', Machine.acquisition_date), extract('month', Machine.acquisition_date))
#     elif time_period == "week":
#         query = query.group_by(extract('year', Machine.acquisition_date), extract('week', Machine.acquisition_date))
#     elif time_period == "day":
#         query = query.group_by(extract('year', Machine.acquisition_date), extract('month', Machine.acquisition_date), extract('day', InventoryBatch.acquisition_date))

#     costs = query.all()
#     if not costs:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No machine data found for the given timeframe")

#     report = {}
#     for cost in costs:
#         if time_period == "year":
#             report_key = f"{cost[0].year}"
#         elif time_period == "month":
#             report_key = f"{cost[0].year}-{cost[0].month:02d}"
#         elif time_period == "week":
#             report_key = f"{cost[0].year}-W{cost[0].isocalendar()[1]:02d}"
#         elif time_period == "day":
#             report_key = f"{cost[0].year}-{cost[0].month:02d}-{cost[0].day:02d}"

#         report_time_period,number_of_machine_acquisition, total_cost = cost[0], cost[1], cost[2]
#         report[report_key] = {
#             "time_period": report_time_period,
#             "number_of_machine_acquisition": number_of_machine_acquisition if number_of_machine_acquisition is not None else 0,
#             "total_cost": total_cost if total_cost is not None else 0
#         }

#     return report

# def plot_machine_cost_report(machine_report: Dict[str, Dict[str, float]],
#     time_period: Literal["year", "month", "week", "day"]
# ):
#     # Extract data for plotting
#     dates = list(machine_report.keys())
#     number_of_sales = [data["number_of_machine_acquisition"] for data in machine_report.values()]
#     total_net_total = [data["total_cost"] for data in machine_report.values()]

#     # Create a figure and axis
#     fig, ax1 = plt.subplots(figsize=(10, 6))

#     # Plot number of sales on the left y-axis
#     ax1.set_xlabel("Time Period")
#     ax1.set_ylabel("Number of Machine Acquisitions", color="skyblue")
#     ax1.bar(dates, number_of_sales, color="skyblue", label="Number of Machine Acquisitions")
#     ax1.set_ylim(ymin=0)
#     ax1.tick_params(axis="y", labelcolor="skyblue")
#     ax1.legend(loc="upper left")

#     # Create a second y-axis for total net total
#     ax2 = ax1.twinx()
#     ax2.set_ylabel("Total Cost", color="orange")
#     ax2.plot(dates, total_net_total, color="orange", label="Total Cost",marker='o')
#     ax2.set_ylim(ymin=0)
#     ax2.tick_params(axis="y", labelcolor="orange")
#     ax2.legend(loc="upper right")

#     # Format the x-axis based on the time period
#     plt.xticks(rotation=45, ha="right")
#     plt.title(f"Machine Cost Report ({time_period.capitalize()})")

#     # Show the plot
#     plt.tight_layout()
#     plt.show()

# cost_report = generate_machine_cost_report("week", datetime(2023, 1, 1), datetime(2024, 12, 31))
# plot_machine_cost_report(cost_report, "week")







def generate_gross_profit_report(
    time_period: Literal["year", "month", "week", "day"],
    start_time: datetime,
    end_time: datetime
) -> Dict[str, Dict[str, float]]:
    # Assume `session` and `Order`, `InventoryBatch`, `Machine` are defined elsewhere

    # Generate sales report
    sales_query = session.query(Order.time_placed,
        func.sum(Order.net_total).label('total_net_total')
    ).filter(Order.time_placed >= start_time, Order.time_placed <= end_time)

    if time_period == "year":
        sales_query = sales_query.group_by(extract('year', Order.time_placed))
    elif time_period == "month":
        sales_query = sales_query.group_by(extract('year', Order.time_placed), extract('month', Order.time_placed))
    elif time_period == "week":
        sales_query = sales_query.group_by(extract('year', Order.time_placed), extract('week', Order.time_placed))
    elif time_period == "day":
        sales_query = sales_query.group_by(extract('year', Order.time_placed), extract('month', Order.time_placed), extract('day', Order.time_placed))

    sales = sales_query.all()
    if not sales:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sales data found for the given timeframe")

    # Generate inventory cost report
    inventory_query = session.query(InventoryBatch.acquisition_date,
        func.sum(InventoryBatch.cost).label('total_cost')
    ).filter(InventoryBatch.acquisition_date >= start_time, InventoryBatch.acquisition_date <= end_time)

    if time_period == "year":
        inventory_query = inventory_query.group_by(extract('year', InventoryBatch.acquisition_date))
    elif time_period == "month":
        inventory_query = inventory_query.group_by(extract('year', InventoryBatch.acquisition_date), extract('month', InventoryBatch.acquisition_date))
    elif time_period == "week":
        inventory_query = inventory_query.group_by(extract('year', InventoryBatch.acquisition_date), extract('week', InventoryBatch.acquisition_date))
    elif time_period == "day":
        inventory_query = inventory_query.group_by(extract('year', InventoryBatch.acquisition_date), extract('month', InventoryBatch.acquisition_date), extract('day', InventoryBatch.acquisition_date))

    inventory_costs = inventory_query.all()
    if not inventory_costs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No inventory cost data found for the given timeframe")

    # Generate machine cost report
    machine_query = session.query(Machine.acquisition_date,
        func.sum(Machine.cost).label('total_cost')
    ).filter(Machine.acquisition_date >= start_time, Machine.acquisition_date <= end_time)

    if time_period == "year":
        machine_query = machine_query.group_by(extract('year', Machine.acquisition_date))
    elif time_period == "month":
        machine_query = machine_query.group_by(extract('year', Machine.acquisition_date), extract('month', Machine.acquisition_date))
    elif time_period == "week":
        machine_query = machine_query.group_by(extract('year', Machine.acquisition_date), extract('week', Machine.acquisition_date))
    elif time_period == "day":
        machine_query = machine_query.group_by(extract('year', Machine.acquisition_date), extract('month', Machine.acquisition_date), extract('day', Machine.acquisition_date))

    machine_costs = machine_query.all()
    if not machine_costs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No machine data found for the given timeframe")

    # Calculate gross profit
    report = {}
    for sale in sales:
        if time_period == "year":
            report_key = f"{sale[0].year}"
        elif time_period == "month":
            report_key = f"{sale[0].year}-{sale[0].month:02d}"
        elif time_period == "week":
            report_key = f"{sale[0].year}-W{sale[0].isocalendar()[1]:02d}"
        elif time_period == "day":
            report_key = f"{sale[0].year}-{sale[0].month:02d}-{sale[0].day:02d}"

        total_net_total = sale[1]
        total_inventory_cost = sum(inventory_cost[1] for inventory_cost in inventory_costs if inventory_cost[0] == sale[0])
        total_machine_cost = sum(machine_cost[1] for machine_cost in machine_costs if machine_cost[0] == sale[0])

        report[report_key] = {
            "time_period": sale[0],
            "total_gross_profit": total_net_total - total_inventory_cost - total_machine_cost
        }

    return report


def plot_gross_profit_report(
        gross_profit_report: Dict[str, Dict[str, float]],
        time_period: Literal["year", "month", "week", "day"]
    ):
        # Extract data for plotting
        dates = list(gross_profit_report.keys())
        total_gross_profit = [data["total_gross_profit"] for data in gross_profit_report.values()]

        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot gross profit
        ax.set_xlabel("Time Period")
        ax.set_ylabel("Total Gross Profit", color="orange")
        ax.plot(dates, total_gross_profit, color="orange", label="Total Gross Profit", marker='o')
        ax.set_ylim(ymin=0)
        ax.tick_params(axis="y", labelcolor="orange")
        ax.legend(loc="upper left")

        # Format the x-axis based on the time period
        plt.xticks(rotation=45, ha="right")
        plt.title(f"Gross Profit Report ({time_period.capitalize()})")

        # Show the plot
        plt.tight_layout()
        plt.show()

gross_profit_report = generate_gross_profit_report("week", datetime(2023, 1, 1), datetime(2024, 12, 31))
plot_gross_profit_report(gross_profit_report, "week")
