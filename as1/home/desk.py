import sqlite3 as sq

con = sq.connect('data_test.db')
cur = con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS Test(
id INTEGER PRIMARY KEY,
amount INTEGER ,
body TEXT,
)''')
con.commit()