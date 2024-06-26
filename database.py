import sqlite3

conn = sqlite3.connect("issues.db")
cursor = conn.cursor()

# Create the 'issues' table if it does not exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL,
        archivedOn DATE DEFAULT NULL
    )
''')

# Creates the "users" table if it does not exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        password TEXT NOT NULL
     )
''')

cursor.execute("INSERT INTO users (username, password) VALUES ('admin', 'pass')")

cursor.execute("PRAGMA table_info(issues)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

if 'archivedOn' not in column_names:
    cursor.execute('ALTER TABLE issues ADD COLUMN archivedOn DATE DEFAULT NULL')

if 'user' not in column_names:
    cursor.execute('ALTER TABLE issues ADD COLUMN user TEXT NOT NULL')

conn.commit()
conn.close()
