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


# Sample data access function as provided
def generate_sales_report(
    time_period: Literal["year", "month", "week", "day"],
    start_time: datetime,
    end_time: datetime
) -> Dict[str, Dict[str, float]]:
    # Assume `session` and `Order` are defined elsewhere
    query = session.query(Order.time_placed,
        func.count(Order.order_id).label('number_of_sales'),
        func.sum(Order.net_total).label('total_net_total')
    ).filter(Order.time_placed >= start_time, Order.time_placed <= end_time)

    if time_period == "year":
        query = query.group_by(extract('year', Order.time_placed))
    elif time_period == "month":
        query = query.group_by(extract('year', Order.time_placed), extract('month', Order.time_placed))
    elif time_period == "week":
        query = query.group_by(extract('year', Order.time_placed), extract('week', Order.time_placed))
    elif time_period == "day":
        query = query.group_by(extract('year', Order.time_placed), extract('month', Order.time_placed), extract('day', Order.time_placed))

    sales = query.all()
    if not sales:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sales data found for the given timeframe")

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

        time_period, number_of_sales, total_net_total = sale[0], sale[1], sale[2]
        report[report_key] = {
            "time_period": time_period,
            "number_of_sales": number_of_sales if number_of_sales is not None else 0,
            "total_net_total": total_net_total if total_net_total is not None else 0
        }

    return report


def plot_sales_report(
    sales_report: Dict[str, Dict[str, float]],
    time_period: Literal["year", "month", "week", "day"]
):
    # Extract data for plotting
    dates = list(sales_report.keys())
    number_of_sales = [data["number_of_sales"] for data in sales_report.values()]
    total_net_total = [data["total_net_total"] for data in sales_report.values()]

    # Create a figure and axis
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot number of sales on the left y-axis
    ax1.set_xlabel("Time Period")
    ax1.set_ylabel("Number of Sales", color="tab:blue")
    ax1.plot(dates, number_of_sales, color="tab:blue", label="Number of Sales")
    ax1.tick_params(axis="y", labelcolor="tab:blue")
    ax1.legend(loc="upper left")

    # Create a second y-axis for total net total
    ax2 = ax1.twinx()
    ax2.set_ylabel("Total Net Total", color="tab:green")
    ax2.plot(dates, total_net_total, color="tab:green", label="Total Net Total")
    ax2.tick_params(axis="y", labelcolor="tab:green")
    ax2.legend(loc="upper right")

    # Format the x-axis based on the time period
    plt.xticks(rotation=45, ha="right")
    plt.title(f"Sales Report ({time_period.capitalize()})")

    # Show the plot
    plt.tight_layout()
    plt.show()

sales_report = generate_sales_report("year", datetime(2023, 1, 1), datetime(2024, 12, 31))

# Plot the sales report
plot_sales_report(sales_report, "year")