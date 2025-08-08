import sqlite3
import dotenv
import os

dotenv.load_dotenv()
db_path = os.getenv("DB_PATH", "db")
EMBED_DB = f"{db_path}/embeds.db"

def init_embeds():
    """initializes the embeds database"""
    with sqlite3.connect(EMBED_DB) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS embeds (
                guild_id INTEGER,
                name TEXT,
                embed TEXT,
                PRIMARY KEY (guild_id, name)
            )
        """)
        conn.commit()