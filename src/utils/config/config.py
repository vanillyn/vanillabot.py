import sqlite3
import dotenv
import os 

dotenv.load_dotenv()
db_path = os.getenv("DB_PATH", "db")
CONF_DB = f"{db_path}/config.db"

def init_config():
    """makes the configuration database"""
    with sqlite3.connect(CONF_DB) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS guild (
                guild_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'en',
                prefix TEXT DEFAULT 'y;',
                welcomeChannel INTEGER,
                welcomeMessage TEXT,
                leaveChannel INTEGER,
                leaveMessage TEXT,
                modLogChannel INTEGER,
                message_type TEXT DEFAULT 'embed'
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS user (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'en',
                message_type TEXT DEFAULT 'embed'
            )
        """)
        conn.commit()

