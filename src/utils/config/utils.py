import sqlite3
import datetime as dt
import json
from typing import Optional, List
from src.utils.config.init import allowed_keys
from src.utils.config.autoresponders import AR_DB
from src.utils.config.embeds import EMBED_DB
from src.utils.config.infractions import MOD_DB
from src.utils.config.config import CONF_DB

# guild and user config management
def set_guild_config(guild_id, key, value):
    """set a configuration value for a guild"""
    
    if key not in allowed_keys.get("guild", []):
        raise ValueError(f"Invalid key: {key}. Allowed keys are: {allowed_keys['guild']}")
    
    if not isinstance(guild_id, int):
        raise ValueError("guild_id must be an integer")
    
    with sqlite3.connect(CONF_DB) as conn:
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
    
    with sqlite3.connect(CONF_DB) as conn:
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
    
    with sqlite3.connect(CONF_DB) as conn:
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
    
    with sqlite3.connect(CONF_DB) as conn:
        c = conn.cursor()
        c.execute(
            f"SELECT {key} FROM user WHERE user_id = ?",
            (user_id,)
        )
        row = c.fetchone()
        return row[0] if row else None
    
def get_language(user_id, guild_id):
    """get the language for a user, and if not, the guild"""
    with sqlite3.connect(CONF_DB) as conn:
        c = conn.cursor()
        c.execute("SELECT language FROM user WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            return row[0]
        c.execute("SELECT language FROM guild WHERE guild_id = ?", (guild_id,))
        row = c.fetchone()
        return row[0] if row else 'en'

# infractions management
def add_infraction(guild_id, user_id, type, reason, duration, issued_by):
    with sqlite3.connect(MOD_DB) as conn:
        timestamp = dt.datetime.now()
        c = conn.cursor()
        c.execute("""
            INSERT INTO infractions (guild_id, user_id, type, reason, duration, issued_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (guild_id, user_id, type, reason, duration, issued_by, timestamp))
        conn.commit()

def get_infractions(guild_id, user_id):
    with sqlite3.connect(MOD_DB) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT type, reason, created_at, duration, issued_by FROM infractions
            WHERE guild_id = ? AND user_id = ?
            ORDER BY created_at DESC
        """, (guild_id, user_id))
        return c.fetchall()
    
def add_note(user_id, note, added_by):
    with sqlite3.connect(MOD_DB) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO notes (user_id, note, added_by, timestamp)
            VALUES (?, ?, ?, datetime('now'))
        """, (user_id, note, added_by))
        conn.commit()
        
def get_notes(user_id):
    with sqlite3.connect(MOD_DB) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT note, added_by, timestamp FROM notes
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """, (user_id,))
        return c.fetchall()
    
# embed management    
def create_embed(guild_id, name, config_dict):
    """create an embed"""
    if not isinstance(guild_id, int):
        raise ValueError("guild_id must be an integer")
    if not isinstance(config_dict, dict):
        raise ValueError("Embed config must be a dictionary")
    
    if len(json.dumps(config_dict)) > 6000:
        raise ValueError("Embed configuration exceeds Discord's 6000 character limit")
    if "fields" in config_dict and len(config_dict["fields"]) > 25:
        raise ValueError("Embed cannot have more than 25 fields")
    for field in config_dict.get("fields", []):
        if len(field.get("name", "")) > 256:
            raise ValueError("Field name exceeds 256 characters")
        if len(field.get("value", "")) > 1024:
            raise ValueError("Field value exceeds 1024 characters")
    if "title" in config_dict and len(config_dict["title"]) > 256:
        raise ValueError("Title exceeds 256 characters")
    if "description" in config_dict and len(config_dict["description"]) > 4096:
        raise ValueError("Description exceeds 4096 characters")
    if "footer" in config_dict and len(config_dict["footer"].get("text", "")) > 2048:
        raise ValueError("Footer text exceeds 2048 characters")
    if "author" in config_dict and len(config_dict["author"].get("name", "")) > 256:
        raise ValueError("Author name exceeds 256 characters")
    
    with sqlite3.connect(EMBED_DB) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO embeds (guild_id, name, embed)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, name) DO UPDATE SET
                embed = excluded.embed
        """, (guild_id, name, json.dumps(config_dict)))
        conn.commit()

def get_embed(guild_id, name):
    """get a single embed"""
    with sqlite3.connect(EMBED_DB) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT embed FROM embeds WHERE guild_id = ? AND name = ?",
            (guild_id, name)
        )
        row = c.fetchone()
        return json.loads(row[0]) if row else None

def delete_embed(guild_id, name):
    """delete an embed"""
    with sqlite3.connect(EMBED_DB) as conn:
        c = conn.cursor()
        c.execute(
            "DELETE FROM embeds WHERE guild_id = ? AND name = ?",
            (guild_id, name)
        )
        conn.commit()
        return c.rowcount > 0

def get_all_embeds(guild_id):
    """get all embeds for a guild"""
    with sqlite3.connect(EMBED_DB) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT name, embed FROM embeds WHERE guild_id = ?",
            (guild_id,)
        )
        return c.fetchall()
    
# autoresponder management

def create_autoresponder(
    guild_id: str,
    name: str,
    trigger: str,
    response: str,
    creator_id: str,
    language: str = "en",
):
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT OR REPLACE INTO autoresponders 
            (guild_id, name, trigger, response, language, creator_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (guild_id, name, trigger, response, language, creator_id),
        )
        conn.commit()


def get_autoresponder(guild_id: str, name: str, language: str = "en") -> Optional[dict]:
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT trigger, response, creator_id 
            FROM autoresponders 
            WHERE guild_id = ? AND name = ? AND language = ?
        """,
            (guild_id, name, language),
        )
        row = c.fetchone()
        if row:
            return {"trigger": row[0], "response": row[1], "creator_id": row[2]}
        return None


def get_all_autoresponders(guild_id: str) -> List[dict]:
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT name, trigger, response, language, creator_id
            FROM autoresponders 
            WHERE guild_id = ?
            ORDER BY name, language
        """,
            (guild_id,),
        )
        rows = c.fetchall()
        return [
            {
                "name": row[0],
                "trigger": row[1],
                "response": row[2],
                "language": row[3],
                "creator_id": row[4],
            }
            for row in rows
        ]


def get_guild_triggers(guild_id: str) -> List[dict]:
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT name, trigger, response, language, creator_id
            FROM autoresponders 
            WHERE guild_id = ?
        """,
            (guild_id,),
        )
        rows = c.fetchall()
        return [
            {
                "name": row[0],
                "trigger": row[1],
                "response": row[2],
                "language": row[3],
                "creator_id": row[4],
            }
            for row in rows
        ]


def update_autoresponder(guild_id: str, name: str, response: str, language: str = "en"):
    """update an existing autoresponder response"""
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        c.execute(
            """
            UPDATE autoresponders 
            SET response = ?
            WHERE guild_id = ? AND name = ? AND language = ?
        """,
            (response, guild_id, name, language),
        )
        conn.commit()
        return c.rowcount > 0


def delete_autoresponder(guild_id: str, name: str) -> bool:
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        c.execute(
            """
            DELETE FROM autoresponders 
            WHERE guild_id = ? AND name = ?
        """,
            (guild_id, name),
        )
        conn.commit()
        return c.rowcount > 0


def autoresponder_exists(guild_id: str, name: str) -> bool:
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT 1 FROM autoresponders 
            WHERE guild_id = ? AND name = ? LIMIT 1
        """,
            (guild_id, name),
        )
        return c.fetchone() is not None

