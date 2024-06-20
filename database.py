import sqlite3

conn = sqlite3.connect("issues.db")
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL
    )
''')

cursor.execute('''
    ALTER TABLE issues
    ADD COLUMN IF NOT EXISTS archivedOn DATE DEFAULT NULL
''')

conn.commit()
conn.close()
