import sqlite3
import dotenv
import os

dotenv.load_dotenv()
db_path = os.getenv("DB_PATH", "db")
AR_DB = f"{db_path}/autoresponders.db"

def init_autoresponders():
    """initializes the autoresponders database"""
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS autoresponders (
                guild_id TEXT,
                name TEXT,
                trigger TEXT,
                response TEXT,
                language TEXT DEFAULT 'en',
                creator_id INTEGER,
                PRIMARY KEY (guild_id, name, language)
            )
        """)
        conn.commit()