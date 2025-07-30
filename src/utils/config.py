import sqlite3
import json
import datetime as dt
DB_PATH = "config.db"

with open("src/utils/keys.json", "r") as f:
    allowed_keys = json.load(f)

def init_config():
    """makes the configuration database"""
    with sqlite3.connect(DB_PATH) as conn:
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


def set_guild_config(guild_id, key, value):
    """set a configuration value for a guild"""
    
    if key not in allowed_keys.get("guild", []):
        raise ValueError(f"Invalid key: {key}. Allowed keys are: {allowed_keys['guild']}")
    
    if not isinstance(guild_id, int):
        raise ValueError("guild_id must be an integer")
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.cursor().execute(f"""
            INSERT INTO guild (guild_id, {key})
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET {key} = excluded.{key}
        """, (guild_id, value))
        conn.commit()


def get_guild_config(guild_id, key):
    """get a configuration value for a guild"""
    if key not in allowed_keys.get("guild", []):
        raise ValueError(f"Invalid key: {key}. Allowed keys are: {allowed_keys['guild']}")
    
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            f"SELECT {key} FROM guild WHERE guild_id = ?",
            (guild_id,)
        )
        row = c.fetchone()
        return row[0] if row else None


def set_user_config(user_id, key, value):
    """set a configuration value for a user"""
    if key not in allowed_keys.get("user", []):
        raise ValueError(f"Invalid key: {key}. Allowed keys are: {allowed_keys['user']}")
    
    if not isinstance(user_id, int):
        raise ValueError("user_id must be an integer")
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.cursor().execute(f"""
            INSERT INTO user (user_id, {key})
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET {key} = excluded.{key}
        """, (user_id, value))
        conn.commit()



def get_user_config(user_id, key):
    """get a configuration value for a user"""
    if key not in allowed_keys.get("user", []):
        raise ValueError(f"Invalid key: {key}. Allowed keys are: {allowed_keys['user']}")
    
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            f"SELECT {key} FROM user WHERE user_id = ?",
            (user_id,)
        )
        row = c.fetchone()
        return row[0] if row else None

def add_infraction(guild_id, user_id, type, reason, duration, issued_by):
    with sqlite3.connect(DB_PATH) as conn:
        timestamp = dt.datetime.now()
        c = conn.cursor()
        c.execute("""
            INSERT INTO infractions (guild_id, user_id, type, reason, duration, issued_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (guild_id, user_id, type, reason, duration, issued_by, timestamp))
        conn.commit()

def get_infractions(guild_id, user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT type, reason, created_at, duration, issued_by FROM infractions
            WHERE guild_id = ? AND user_id = ?
            ORDER BY created_at DESC
        """, (guild_id, user_id))
        return c.fetchall()
    
def add_note(user_id, note, added_by):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO notes (user_id, note, added_by, timestamp)
            VALUES (?, ?, ?, datetime('now'))
        """, (user_id, note, added_by))
        conn.commit()
        
def get_notes(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT note, added_by, timestamp FROM notes
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """, (user_id,))
        return c.fetchall()
    
def get_language(user_id, guild_id):
    """get the language for a user, and if not, the guild"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT language FROM user WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            return row[0]
        c.execute("SELECT language FROM guild WHERE guild_id = ?", (guild_id,))
        row = c.fetchone()
        return row[0] if row else 'en'