# database.py
import sqlite3

DB_FILE = "errp.db"

def get_db():
    """SQLite 연결 객체 반환 및 딕셔너리 Row 형태 설정"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """테이블 초기화"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            phone TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            brand TEXT,
            store_code TEXT,
            theme TEXT,
            date TEXT,
            time TEXT,
            run_date TEXT,
            run_time TEXT,
            img TEXT,
            status TEXT DEFAULT '대기중'
        )
    """)
    
    default_users = [
        ("admin", "1234", "관리자", "01012345678"),
        ("user1", "1234", "홍길동", "01099998888")
    ]
    for u in default_users:
        try:
            cursor.execute("INSERT INTO users (username, password, name, phone) VALUES (?, ?, ?, ?)", u)
        except sqlite3.IntegrityError:
            pass
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()