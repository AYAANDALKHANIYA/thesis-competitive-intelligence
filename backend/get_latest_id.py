import sqlite3

def get_latest():
    conn = sqlite3.connect('market_intelligence.db')
    cursor = conn.cursor()
    # Find tables that have 'id' or 'analysis'
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        tname = table[0]
        if 'analysis' in tname or 'run' in tname:
            print(f"Table: {tname}")
            cursor.execute(f"PRAGMA table_info({tname})")
            print([c[1] for c in cursor.fetchall()])
            try:
                cursor.execute(f"SELECT id FROM {tname} ORDER BY id DESC LIMIT 1")
                res = cursor.fetchone()
                print(f"Latest ID in {tname}: {res}")
            except:
                pass

get_latest()
