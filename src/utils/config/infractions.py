import sqlite3
import dotenv
import os

dotenv.load_dotenv()
db_path = os.getenv("DB_PATH", "db")
MOD_DB = f"{db_path}/infractions.db"

def init_infractions():
    """initializes the infractions database"""
    with sqlite3.connect(MOD_DB) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS infractions (
                guild_id INTEGER,
                user_id INTEGER,
                type TEXT,
                reason TEXT,
                duration TEXT,
                issued_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id, created_at)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                user_id INTEGER,
                note TEXT,
                added_by INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, timestamp)
            )
        """)
        conn.commit()