import sqlite3

conn = sqlite3.connect('ecommerce/ecommerce.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Tables:', tables)
if tables:
    cursor.execute('SELECT * FROM user')
    users = cursor.fetchall()
    print('Users:', users)
    cursor.execute('SELECT * FROM cart_item')
    cart = cursor.fetchall()
    print('Cart items:', cart)
conn.close()
