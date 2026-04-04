import sqlite3


def init_db():
    conn = sqlite3.connect('cafe_work.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS workers 
                      (user_id INTEGER PRIMARY KEY, 
                       full_name TEXT, 
                       phone TEXT, 
                       filial TEXT, 
                       start_time TEXT)''')
    conn.commit()
    conn.close()


def add_worker_to_db(u_id, name, phone, filial, time):
    conn = sqlite3.connect('cafe_work.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO workers VALUES (?, ?, ?, ?, ?)",
                   (u_id, name, phone, filial, time))
    conn.commit()
    conn.close()


def get_all_workers():
    conn = sqlite3.connect('cafe_work.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workers")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_worker_by_id(user_id):
    conn = sqlite3.connect('cafe_work.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workers WHERE user_id = ?", (user_id,))
    worker = cursor.fetchone()
    conn.close()
    return worker

import sqlite3

# Ishchini ID bo'yicha o'chirish
def delete_worker_from_db(user_id):
    conn = sqlite3.connect('cafe_work.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM workers WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# Ishchining vaqtini yangilash (eng ko'p kerak bo'ladigani)
def update_worker_time(user_id, new_time):
    conn = sqlite3.connect('cafe_work.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE workers SET start_time = ? WHERE user_id = ?", (new_time, user_id))
    conn.commit()
    conn.close()
init_db()