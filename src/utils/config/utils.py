import sqlite3
import datetime as dt
import json
from src.utils.config import allowed_keys
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

def create_embed(guild_id, name, embed_config, language, creator_id, editors='', contributors='', editor_role=None, edit_permissions='edit,delete,add_language'):
    """Create a new embed"""
    with sqlite3.connect(EMBED_DB) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO embeds (guild_id, name, embed, language, creator_id, editors, contributors, editor_role, edit_permissions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (guild_id, name, json.dumps(embed_config), language, creator_id, editors, contributors, editor_role, edit_permissions))
        conn.commit()

def update_embed(guild_id, name, language, embed_config=None, **kwargs):
    """Update an existing embed"""
    with sqlite3.connect(EMBED_DB) as conn:
        c = conn.cursor()
        fields = []
        values = []
        if embed_config is not None:
            fields.append("embed=?")
            values.append(json.dumps(embed_config))
        for key, value in kwargs.items():
            fields.append(f"{key}=?")
            values.append(value)
        fields_str = ', '.join(fields)
        values += [guild_id, name, language]
        c.execute(f"""
            UPDATE embeds SET {fields_str}
            WHERE guild_id=? AND name=? AND language=?
        """, values)
        updated = c.rowcount > 0
        conn.commit()
        return updated

def delete_embed(guild_id, name):
    """Delete an embed (all languages)"""
    with sqlite3.connect(EMBED_DB) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM embeds WHERE guild_id=? AND name=?", (guild_id, name))
        deleted = c.rowcount > 0
        conn.commit()
        return deleted

def get_embed(guild_id, name, language):
    """Get an embed for a specific language"""
    with sqlite3.connect(EMBED_DB) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT guild_id, name, embed, language, creator_id, editors, contributors, editor_role, edit_permissions
            FROM embeds WHERE guild_id=? AND name=? AND language=?
        """, (guild_id, name, language))
        row = c.fetchone()
        if row:
            return {
                'guild_id': row[0],
                'name': row[1],
                'embed': json.loads(row[2]),
                'language': row[3],
                'creator_id': row[4],
                'editors': row[5],
                'contributors': row[6],
                'editor_role': row[7],
                'edit_permissions': row[8]
            }
        return None

def get_all_embeds(guild_id):
    """Get all embeds for a guild"""
    with sqlite3.connect(EMBED_DB) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT guild_id, name, embed, language, creator_id, editors, contributors, editor_role, edit_permissions
            FROM embeds WHERE guild_id=?
        """, (guild_id,))
        rows = c.fetchall()
        return [{
            'guild_id': row[0],
            'name': row[1],
            'embed': json.loads(row[2]),
            'language': row[3],
            'creator_id': row[4],
            'editors': row[5],
            'contributors': row[6],
            'editor_role': row[7],
            'edit_permissions': row[8]
        } for row in rows]
    
# autoresponder management

def create_autoresponder(guild_id, name, trigger, response, creator_id, language, editors='', contributors='', editor_role=None, edit_permissions='edit,delete,add_language', arguments='none'):
    """Create a new autoresponder"""
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO autoresponders (guild_id, name, trigger, response, language, creator_id, editors, contributors, editor_role, edit_permissions, arguments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (guild_id, name, trigger, response, language, creator_id, editors, contributors, editor_role, edit_permissions, arguments))
        conn.commit()

def update_autoresponder(guild_id, name, language, **kwargs):
    """Update an existing autoresponder"""
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        fields = ', '.join(f"{key}=?" for key in kwargs)
        values = list(kwargs.values()) + [guild_id, name, language]
        c.execute(f"""
            UPDATE autoresponders SET {fields}
            WHERE guild_id=? AND name=? AND language=?
        """, values)
        updated = c.rowcount > 0
        conn.commit()
        return updated

def delete_autoresponder(guild_id, name):
    """Delete an autoresponder (all languages)"""
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM autoresponders WHERE guild_id=? AND name=?", (guild_id, name))
        deleted = c.rowcount > 0
        conn.commit()
        return deleted

def autoresponder_exists(guild_id, name):
    """Check if an autoresponder exists"""
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM autoresponders WHERE guild_id=? AND name=?", (guild_id, name))
        return c.fetchone() is not None

def get_autoresponder(guild_id, name, language):
    """Get an autoresponder for a specific language"""
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT guild_id, name, trigger, response, language, creator_id, editors, contributors, editor_role, edit_permissions, arguments
            FROM autoresponders WHERE guild_id=? AND name=? AND language=?
        """, (guild_id, name, language))
        row = c.fetchone()
        if row:
            return {
                'guild_id': row[0], 'name': row[1], 'trigger': row[2], 'response': row[3],
                'language': row[4], 'creator_id': row[5], 'editors': row[6], 'contributors': row[7],
                'editor_role': row[8], 'edit_permissions': row[9], 'arguments': row[10]
            }
        return None

def get_all_autoresponders(guild_id):
    """Get all autoresponders for a guild"""
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT guild_id, name, trigger, response, language, creator_id, editors, contributors, editor_role, edit_permissions, arguments
            FROM autoresponders WHERE guild_id=?
        """, (guild_id,))
        rows = c.fetchall()
        return [{
            'guild_id': row[0], 'name': row[1], 'trigger': row[2], 'response': row[3],
            'language': row[4], 'creator_id': row[5], 'editors': row[6], 'contributors': row[7],
            'editor_role': row[8], 'edit_permissions': row[9], 'arguments': row[10]
        } for row in rows]

def get_guild_triggers(guild_id):
    """Get all triggers for a guild"""
    with sqlite3.connect(AR_DB) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT name, trigger
            FROM autoresponders WHERE guild_id=?
        """, (guild_id,))
        rows = c.fetchall()
        return [{'name': row[0], 'trigger': row[1]} for row in rows]