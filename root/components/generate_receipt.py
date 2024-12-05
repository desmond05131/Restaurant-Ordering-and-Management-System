from zpl import Label
import os
from PIL import Image


def generate_receipt(receipt_info):
    l = Label(150, 70)  # Adjust label size and dpmm as needed
    y_pos = 4

    # Header section
    l.origin(5, y_pos)
    l.write_text("Example: Tea Garden", char_height=4, char_width=4, line_width=60, justification='C')
    l.endorigin()
    y_pos += 6

    l.origin(5, y_pos)
    l.write_text("Example Address: Tea Garden Taman Gaya", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 3

    l.origin(5, y_pos)
    l.write_text("2, JLN GAYA 28, TMN GAYA,", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 3

    l.origin(5, y_pos)
    l.write_text("81800 ULU TIRAM, JOHOR", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 3

    l.origin(5, y_pos)
    l.write_text("TEL: 016_7114235", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 3

    l.origin(5, y_pos)
    l.write_text("TEA GARDEN RESTAURANT (MY) Sdn Bhd", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 3

    l.origin(5, y_pos)
    l.write_text("(962457-P)", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 3

    l.origin(5, y_pos)
    l.write_text("(SST ID: J31-1808-31029890)", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 5

    l.origin(5, y_pos)
    l.write_text("(INVOICE)", char_height=3, char_width=3, line_width=60, justification='C')
    l.endorigin()
    y_pos += 6

    # Invoice and Table details
    l.origin(5, y_pos)
    l.write_text(f" Invoice No: {receipt_info['invoice_number']}", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()
    y_pos += 3

    l.origin(5, y_pos)
    l.write_text(f" Table No: {receipt_info['table_number']}", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()
    y_pos += 5

    l.origin(5, y_pos)
    l.write_text(f" Date Time: {receipt_info['date_time']}", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()
    y_pos += 5


    l.origin(5, y_pos)
    l.write_text("-" * 40, char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 2

    l.origin(5, y_pos)
    l.write_text("( QTY ITEM)", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()

    l.origin(5, y_pos)
    l.write_text("(RM )", char_height=2, char_width=2, line_width=60, justification='R')
    l.endorigin()
    y_pos += 2

    l.origin(5, y_pos)
    l.write_text("-" * 40, char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 4

    initial_y_pos_1 = y_pos
    initial_y_pos_2 = y_pos

    # Itemized list
    for item in receipt_info['items']:
        l.origin(5, initial_y_pos_1)
        l.write_text(f" {item['quantity']} {item['name']}", char_height=2, char_width=2, line_width=60, justification='L')
        l.endorigin()
        initial_y_pos_1 += 4

    for item in receipt_info['items']:
        l.origin(5, initial_y_pos_2)
        l.write_text(f"{item['price']:.2f} ", char_height=2, char_width=2, line_width=60, justification='R')
        l.endorigin()
        initial_y_pos_2 += 4
    
    y_pos += (initial_y_pos_1 - y_pos)  # Space before subtotal
    # Add a separator line
    l.origin(5, y_pos)
    l.write_text("-" * 40, char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 4
    # Add a separator line before totals
    l.origin(5, y_pos)
    l.write_text("-" * 40, char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 4

    # Totals section
    l.origin(5, y_pos)
    l.write_text(" Voucher Applied", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()

    l.origin(5, y_pos)
    l.write_text(f"{receipt_info['voucher_applied']} ", char_height=2, char_width=2, line_width=60, justification='R')
    l.endorigin()
    y_pos += 4

    l.origin(5, y_pos)
    l.write_text(" Subtotal", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()

    l.origin(5, y_pos)
    l.write_text(f"{receipt_info['subtotal']:.2f} ", char_height=2, char_width=2, line_width=60, justification='R')
    l.endorigin()
    y_pos += 4

    l.origin(5, y_pos)
    l.write_text(" Sales/Gov Tax - 6%", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()

    l.origin(5, y_pos)
    l.write_text(f"{receipt_info['sales_tax']:.2f} ", char_height=2, char_width=2, line_width=60, justification='R')
    l.endorigin()
    y_pos += 4

    l.origin(5, y_pos)
    l.write_text(" Service Charge - 6%", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()

    l.origin(5, y_pos)
    l.write_text(f"{receipt_info['service_charge']:.2f} ", char_height=2, char_width=2, line_width=60, justification='R')
    l.endorigin()
    y_pos += 4

    l.origin(5, y_pos)
    l.write_text(" Rounding Adj", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()

    l.origin(5, y_pos)
    l.write_text(f"{receipt_info['rounding_adjustment']:.2f} ", char_height=2, char_width=2, line_width=60, justification='R')
    l.endorigin()
    y_pos += 4

    l.origin(5, y_pos)
    l.write_text(" NET TOTAL", char_height=3, char_width=3, line_width=60, justification='L')
    l.endorigin()

    l.origin(5, y_pos)
    l.write_text(f"{receipt_info['net_total']:.2f} ", char_height=3, char_width=3, line_width=60, justification='R')
    l.endorigin()
    y_pos += 8

    l.origin(5, y_pos)
    l.write_text("-" * 40, char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 4

    l.origin(5, y_pos)
    l.write_text(" Paying Method", char_height=2, char_width=2, line_width=60, justification='L')
    l.endorigin()

    l.origin(5, y_pos)
    l.write_text(f"{receipt_info['paying_method']} ", char_height=2, char_width=2, line_width=60, justification='R')
    l.endorigin()
    y_pos += 4

    # Footer section
    l.origin(5, y_pos)
    l.write_text("Thank you and see you again!", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 4

    l.origin(5, y_pos)
    l.write_text("Bring this bill back within the next 10 days", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()
    y_pos += 4

    l.origin(5, y_pos)
    l.write_text("and get 15% discount on that day's food bill...", char_height=2, char_width=2, line_width=60, justification='C')
    l.endorigin()

    # Save ZPL output
    with open("./receipt.zpl", "w") as file:
        file.write(l.dumpZPL())
        print(l.dumpZPL())  # Print ZPL to console for debugging

    return l
