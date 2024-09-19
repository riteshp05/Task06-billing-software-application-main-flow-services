import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import pandas as pd
from reportlab.pdfgen import canvas
import datetime

# Load Netflix Dataset
netflix_dataset_path = '/Users/riteshreddy/Desktop/MainFlow Python Developer/Task 6/Python Dataset/netflix.csv'  # Path to the uploaded dataset
df_netflix = pd.read_csv(netflix_dataset_path)

# Extract movie titles from the dataset for the dropdown
predefined_movies = df_netflix['title'].dropna().tolist()

# Database setup
def setup_db():
    conn = sqlite3.connect("netflix_billing.db")
    cursor = conn.cursor()

    # Create Netflix-like products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        genres TEXT,
        language TEXT,
        imdb_score REAL,
        premiere TEXT,
        runtime INTEGER,
        year INTEGER
    )
    """)

    # Create customers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        contact TEXT
    )
    """)

    # Create transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        date TEXT,
        total REAL,
        discount REAL,
        tax REAL,
        final_total REAL,
        FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
    )
    """)
    
    conn.commit()
    conn.close()

# Add Movie to Cart
cart = []

def add_to_cart():
    movie_title = movie_title_combobox.get()
    quantity = movie_quantity_entry.get()

    if movie_title and quantity:
        try:
            movie_row = df_netflix[df_netflix['title'].str.lower() == movie_title.lower()].iloc[0]
            title = movie_row['title']
            imdb_score = movie_row['imdb_score']
            runtime = movie_row['runtime']
            year = movie_row['year']
            
            # Update the cart
            cart.append({
                'title': title,
                'imdb_score': imdb_score,
                'runtime': runtime,
                'year': year,
                'quantity': int(quantity),
                'total': int(quantity) * 100  # Assuming each movie costs 100 units
            })

            # Update the total
            update_total()

            movie_title_combobox.set('')
            movie_quantity_entry.delete(0, tk.END)
        except IndexError:
            messagebox.showerror("Error", "Movie not found in dataset.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    else:
        messagebox.showerror("Error", "Movie title and Quantity are required!")

# Update Total Calculation
def update_total():
    total = sum(item['total'] for item in cart)
    discount = float(discount_entry.get()) if discount_entry.get() else 0
    tax_rate = float(tax_entry.get()) if tax_entry.get() else 0

    # Calculate tax and final total
    tax_amount = (total - discount) * tax_rate / 100
    final_total = total - discount + tax_amount

    total_label.config(text=f"Total: {total:.2f}")
    discount_label.config(text=f"Discount: {discount:.2f}")
    tax_label.config(text=f"Tax: {tax_amount:.2f}")
    final_total_label.config(text=f"Final Total: {final_total:.2f}")

# Print and Generate Bill
def print_bill():
    customer_name = customer_name_entry.get()
    contact = customer_contact_entry.get()
    
    if cart and customer_name:
        bill_text = f"Bill for {customer_name} - Contact: {contact}\n\n"
        bill_text += "Title\tQty\tPrice\n"
        bill_text += "-"*30 + "\n"

        for item in cart:
            bill_text += f"{item['title']}\t{item['quantity']}\t{item['total']}\n"
        
        bill_text += "\n" + "-"*30
        bill_text += f"\nTotal: {total_label.cget('text')}"
        bill_text += f"\nDiscount: {discount_label.cget('text')}"
        bill_text += f"\nTax: {tax_label.cget('text')}"
        bill_text += f"\nFinal Total: {final_total_label.cget('text')}\n"

        # Display the bill in a message box or terminal
        messagebox.showinfo("Bill", bill_text)

        # Generate PDF invoice as well
        generate_invoice()
    else:
        messagebox.showerror("Error", "Cart is empty or customer details are missing!")

# Generate Invoice (PDF)
def generate_invoice():
    customer_name = customer_name_entry.get()
    contact = customer_contact_entry.get()
    discount = float(discount_entry.get()) if discount_entry.get() else 0
    tax_rate = float(tax_entry.get()) if tax_entry.get() else 0

    if customer_name and contact:
        try:
            conn = sqlite3.connect("netflix_billing.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO customers (name, contact) VALUES (?, ?)", (customer_name, contact))
            customer_id = cursor.lastrowid
            total = sum(item['total'] for item in cart)
            tax_amount = (total - discount) * tax_rate / 100
            final_total = total - discount + tax_amount
            date = str(datetime.date.today())

            cursor.execute("INSERT INTO transactions (customer_id, date, total, discount, tax, final_total) VALUES (?, ?, ?, ?, ?, ?)", 
                           (customer_id, date, total, discount, tax_amount, final_total))
            conn.commit()

            # Generate PDF invoice
            c = canvas.Canvas(f"invoice_{customer_name}.pdf")
            c.drawString(100, 750, f"Invoice for {customer_name}")
            c.drawString(100, 730, f"Contact: {contact}")
            c.drawString(100, 710, f"Date: {date}")
            c.drawString(100, 690, f"Total Amount: {total}")
            c.drawString(100, 670, f"Discount: {discount}")
            c.drawString(100, 650, f"Tax: {tax_amount}")
            c.drawString(100, 630, f"Final Total: {final_total}")
            c.showPage()
            c.save()

            messagebox.showinfo("Success", f"Invoice generated for {customer_name}!")
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    else:
        messagebox.showerror("Error", "Customer details are required!")

# GUI setup
root = tk.Tk()
root.title("Netflix Billing Software")

# Predefined Movie Title Entry for Selection
tk.Label(root, text="Movie Title").grid(row=0, column=0)
movie_title_combobox = ttk.Combobox(root, values=predefined_movies)
movie_title_combobox.grid(row=0, column=1)

tk.Label(root, text="Quantity").grid(row=1, column=0)
movie_quantity_entry = tk.Entry(root)
movie_quantity_entry.grid(row=1, column=1)

tk.Button(root, text="Add to Cart", command=add_to_cart).grid(row=2, column=1)

# Customer Details Section
tk.Label(root, text="Customer Name").grid(row=3, column=0)
customer_name_entry = tk.Entry(root)
customer_name_entry.grid(row=3, column=1)

tk.Label(root, text="Customer Contact").grid(row=4, column=0)
customer_contact_entry = tk.Entry(root)
customer_contact_entry.grid(row=4, column=1)

# Discount and Tax Section
tk.Label(root, text="Discount (%)").grid(row=5, column=0)
discount_entry = tk.Entry(root)
discount_entry.grid(row=5, column=1)

tk.Label(root, text="Tax Rate (%)").grid(row=6, column=0)
tax_entry = tk.Entry(root)
tax_entry.grid(row=6, column=1)

# Total Calculation and Invoice Generation
total_label = tk.Label(root, text="Total: 0")
total_label.grid(row=7, column=0)

discount_label = tk.Label(root, text="Discount: 0")
discount_label.grid(row=8, column=0)

tax_label = tk.Label(root, text="Tax: 0")
tax_label.grid(row=9, column=0)

final_total_label = tk.Label(root, text="Final Total: 0")
final_total_label.grid(row=10, column=0)

tk.Button(root, text="Generate Invoice", command=generate_invoice).grid(row=11, column=1)
tk.Button(root, text="Print Bill", command=print_bill).grid(row=12, column=1)

# Initialize database
setup_db()

root.mainloop()

