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
        # new server config columns, will be added if they dont exist in the existing db
        try:
            c.execute("ALTER TABLE guild ADD COLUMN autoresponder_edit_role INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE guild ADD COLUMN autoresponder_edit_permission TEXT DEFAULT 'send_messages'")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE guild ADD COLUMN embed_edit_role INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE guild ADD COLUMN embed_edit_permission TEXT DEFAULT 'manage_server'")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE guild ADD COLUMN server_config_role INTEGER")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE guild ADD COLUMN staff_role INTEGER")
        except sqlite3.OperationalError:
            pass
        conn.commit()