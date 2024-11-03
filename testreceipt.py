
from zpl import Label
import os
from PIL import Image


def generate_receipt(receipt_info):
    l = Label(150, 60)  # Adjust label size and dpmm as needed
    y_pos = 4

    # Header section
    l.origin(0, y_pos)
    l.write_text("Example: Tea Garden", char_height=4, char_width=4, line_width=60, justification='C')
    l.endorigin()
    y_pos += 6

    l.origin(0, y_pos)
    l.write_text("Example Address: Tea Garden Taman Gaya", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 3

    l.origin(0, y_pos)
    l.write_text("2, JLN GAYA 28, TMN GAYA,", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 3

    l.origin(0, y_pos)
    l.write_text("81800 ULU TIRAM, JOHOR", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 3

    l.origin(0, y_pos)
    l.write_text("TEL: 016_7114235", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 3

    l.origin(0, y_pos)
    l.write_text("TEA GARDEN RESTAURANT (MY) Sdn Bhd", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 3

    l.origin(0, y_pos)
    l.write_text("(962457-P)", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 3

    l.origin(0, y_pos)
    l.write_text("(SST ID: J31-1808-31029890)", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 5

    l.origin(0, y_pos)
    l.write_text("(INVOICE)", char_height=3, char_width=3, line_width=60, justification='C')
    l.endorigin()
    y_pos += 6

    # Invoice and Table details
    l.origin(0, y_pos)
    l.write_text(f" Invoice No: {receipt_info['invoice_number']}       {receipt_info['date']}", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()
    y_pos += 3

    l.origin(0, y_pos)
    l.write_text(f" Table No: {receipt_info['table_number']}       {receipt_info['time']}", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()
    y_pos += 5

    l.origin(0, y_pos)
    l.write_text("-" * 40, char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 2

    l.origin(0, y_pos)
    l.write_text("( QTY ITEM)", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()

    l.origin(0, y_pos)
    l.write_text("(RM )", char_height=2, char_width=2, line_width=60, justification='R')
    l.endorigin()
    y_pos += 2

    l.origin(0, y_pos)
    l.write_text("-" * 40, char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 4

    initial_y_pos_1 = y_pos
    initial_y_pos_2 = y_pos

    # Itemized list
    for item in receipt_info['items']:
        l.origin(0, initial_y_pos_1)
        l.write_text(f" {item['quantity']} {item['name']}", char_height=2, char_width=2, line_width=60, justification='L')
        l.endorigin()
        initial_y_pos_1 += 4

    for item in receipt_info['items']:
        l.origin(0, initial_y_pos_2)
        l.write_text(f"{item['price']:.2f} ", char_height=2, char_width=2, line_width=60, justification='R')
        l.endorigin()
        initial_y_pos_2 += 4
    
    y_pos += (initial_y_pos_1 - y_pos)  # Space before subtotal
    # Add a separator line
    l.origin(0, y_pos)
    l.write_text("-" * 40, char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 4
    # Add a separator line before totals
    l.origin(0, y_pos)
    l.write_text("-" * 40, char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 4
    # Totals section
    l.origin(0, y_pos)
    l.write_text(" Voucher Applied", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()

    l.origin(0, y_pos)
    l.write_text(f"{receipt_info['voucher_applied']} ", char_height=2, char_width=2, line_width=60, justification='R')
    l.endorigin()
    y_pos += 4

    l.origin(0, y_pos)
    l.write_text(" Subtotal", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()


    l.origin(0, y_pos)
    l.write_text(f"{receipt_info['subtotal']:.2f} ", char_height=2, char_width=2, line_width=60, justification='R')
    l.endorigin()
    y_pos += 4

    l.origin(0, y_pos)
    l.write_text(" Sales/Gov Tax - 6%", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()

    l.origin(0, y_pos)
    l.write_text(f"{receipt_info['sales_tax']:.2f} ", char_height=2, char_width=2, line_width=60, justification='R')
    l.endorigin()
    y_pos += 4

    l.origin(0, y_pos)
    l.write_text(" Service Charge - 6%", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()

    l.origin(0, y_pos)
    l.write_text(f"{receipt_info['service_charge']:.2f} ", char_height=2, char_width=2, line_width=60, justification='R')
    l.endorigin()
    y_pos += 4

    l.origin(0, y_pos)
    l.write_text(" Rounding Adj", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()

    l.origin(0, y_pos)
    l.write_text(f"{receipt_info['rounding_adjustment']:.2f} ", char_height=2, char_width=2, line_width=60, justification='R')
    l.endorigin()
    y_pos += 4

    l.origin(0, y_pos)
    l.write_text(" NET TOTAL", char_height=3, char_width=3, line_width=60, justification='L')
    l.endorigin()

    l.origin(0, y_pos)
    l.write_text(f"{receipt_info['net_total']:.2f} ", char_height=3, char_width=3, line_width=60, justification='R')
    l.endorigin()
    y_pos += 8

    l.origin(0, y_pos)
    l.write_text("-" * 40, char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 4

    l.origin(0, y_pos)
    l.write_text(" Paying Method", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()

    l.origin(0, y_pos)
    l.write_text(f"{receipt_info['paying_method']} ", char_height=2, char_width=2, line_width=60, justification='R')
    l.endorigin()
    y_pos += 4

    # Footer section
    l.origin(0, y_pos)
    l.write_text("Thank you and see you again!", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 4

    l.origin(0, y_pos)
    l.write_text("Bring this bill back within the next 10 days", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 4

    l.origin(0, y_pos)
    l.write_text("and get 15% discount on that day's food bill...", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()

    # Save ZPL output
    with open("./receipt.zpl", "w") as file:
        file.write(l.dumpZPL())
        print(l.dumpZPL())  # Print ZPL to console for debugging

    return l

# Example receipt data to test the function
receipt_info = {
    "invoice_number": "08000008",
    "date": "09/04/08",
    "table_number": "25",
    "time": "12:45",
    "items": [
        {"quantity": 2, "name": "Carlsberg Bottle", "price": 16.00},
        {"quantity": 3, "name": "Heineken Draft Standard", "price": 24.60},
        {"quantity": 1, "name": "Heineken Draft Half Liter", "price": 15.20},
        {"quantity": 2, "name": "Carlsberg Bucket (5 bottles)", "price": 80.00},
        {"quantity": 4, "name": "Grilled Chicken Breast", "price": 74.00},
        {"quantity": 3, "name": "Sirloin Steak", "price": 96.00},
        {"quantity": 1, "name": "Coke", "price": 3.50},
        {"quantity": 5, "name": "Ice Cream", "price": 18.00},
    ],
    "voucher_applied": "DISCOUNT10",
    "subtotal": 327.30,
    "sales_tax": 16.36,
    "service_charge": 32.73,
    "rounding_adjustment": 0.01,
    "net_total": 376.40,
    "paying_method": "CASH",
    
}

# Generate the receipt
receipt_label = generate_receipt(receipt_info)

# Print the ZPL code
print(receipt_label.dumpZPL())

# Preview the label
receipt_label.preview()
