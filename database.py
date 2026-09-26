import sqlite3
import datetime

DB_NAME = 'shop.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'available',
            buyer_id INTEGER DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sold_at TIMESTAMP DEFAULT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT
        )
    ''')
    
    cursor.execute("INSERT OR IGNORE INTO settings (setting_key, setting_value) VALUES ('price', '۱۵۰,۰۰۰ تومان')")
    cursor.execute("INSERT OR IGNORE INTO settings (setting_key, setting_value) VALUES ('card_number', '۱۲۳۴-۵۶۷۸-۱۲۳۴-۵۶۷۸')")
    cursor.execute("INSERT OR IGNORE INTO settings (setting_key, setting_value) VALUES ('card_name', 'نامشخص')")
    
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT setting_value FROM settings WHERE setting_key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET setting_value = ? WHERE setting_key = ?", (value, key))
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    return [u[0] for u in users]

def add_licenses(codes):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    added_count = 0 
    for code in codes:
        if code.strip():
            try:
                cursor.execute("INSERT OR IGNORE INTO licenses (code) VALUES (?)", (code.strip(),))
                if cursor.rowcount > 0:
                    added_count += 1
            except:
                pass
    conn.commit()
    conn.close()
    return added_count 

def get_available_count():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM licenses WHERE status = 'available'")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_total_sold_count():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM licenses WHERE status = 'sold'")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def sell_license(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, code FROM licenses WHERE status = 'available' LIMIT 1")
    result = cursor.fetchone()
    if result:
        lic_id, lic_code = result
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE licenses SET status = 'sold', buyer_id = ?, sold_at = ? WHERE id = ?", (user_id, current_time, lic_id))
        conn.commit()
        conn.close()
        return lic_code
    conn.close()
    return None

def get_user_purchases(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT code, sold_at FROM licenses WHERE buyer_id = ?", (user_id,))
    purchases = cursor.fetchall()
    conn.close()
    return purchases

def check_license_status(code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT status, buyer_id, sold_at FROM licenses WHERE code = ?", (code,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_all_available_licenses():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM licenses WHERE status = 'available'")
    codes = cursor.fetchall()
    conn.close()
    return [c[0] for c in codes]

def get_all_sold_licenses():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT code, buyer_id, sold_at FROM licenses WHERE status = 'sold'")
    codes = cursor.fetchall()
    conn.close()
    return codes