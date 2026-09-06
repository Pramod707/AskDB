import sqlite3

# step1 : create a database
conn = sqlite3.connect("AskDb_test.db")
cursor = conn.cursor()
# step2: create a table
# tables 1.customers , orders , products, order_items
cursor.execute(
    """
    create table customers(customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    city TEXT,
    join_date TEXT
    )
    """
)
# step3 : enter the dummy data
