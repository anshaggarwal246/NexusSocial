"""
Initializes and populates social_media.db from the project SQL files.
"""
import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), 'social_media.db')

def split_sql_statements(sql_text):
    statements = []
    current = []
    in_single_quote = False
    in_double_quote = False
    i = 0
    n = len(sql_text)
    while i < n:
        c = sql_text[i]
        if c == "'" and not in_double_quote:
            if in_single_quote and i + 1 < n and sql_text[i+1] == "'":
                current.append("''")
                i += 2
                continue
            elif in_single_quote and i > 0 and sql_text[i-1] == '\\':
                current.append(c)
                i += 1
                continue
            in_single_quote = not in_single_quote
            current.append(c)
        elif c == '"' and not in_single_quote:
            if in_double_quote and i > 0 and sql_text[i-1] == '\\':
                current.append(c)
                i += 1
                continue
            in_double_quote = not in_double_quote
            current.append(c)
        elif c == ';' and not in_single_quote and not in_double_quote:
            stmt = ''.join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
        else:
            current.append(c)
        i += 1
    rem = ''.join(current).strip()
    if rem:
        statements.append(rem)
    return statements

def init_database(force=False):
    if os.path.exists(DB_PATH) and not force:
        # Check if already populated
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM post")
            count = cur.fetchone()[0]
            conn.close()
            if count > 0:
                print(f"[DB] Database already initialized with {count} posts.")
                return DB_PATH
        except Exception:
            pass

    print("[DB] Initializing database and importing SQL seeds...")
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    schema_sqlite = '''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(255) UNIQUE NOT NULL,
        profile_photo_url VARCHAR(255) DEFAULT 'https://picsum.photos/100',
        bio VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        email VARCHAR(30) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS photos (
        photo_id INTEGER PRIMARY KEY AUTOINCREMENT,
        photo_url VARCHAR(255) NOT NULL,
        post_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        size FLOAT
    );

    CREATE TABLE IF NOT EXISTS videos (
        video_id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_url VARCHAR(255) NOT NULL,
        post_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        size FLOAT
    );

    CREATE TABLE IF NOT EXISTS post (
        post_id INTEGER PRIMARY KEY AUTOINCREMENT,
        photo_id INTEGER,
        video_id INTEGER,
        user_id INTEGER NOT NULL,
        caption VARCHAR(200), 
        location VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS comments (
        comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        comment_text VARCHAR(255) NOT NULL,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS post_likes (
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(user_id, post_id)
    );

    CREATE TABLE IF NOT EXISTS comment_likes (
        user_id INTEGER NOT NULL,
        comment_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(user_id, comment_id)
    );

    CREATE TABLE IF NOT EXISTS follows (
        follower_id INTEGER NOT NULL,
        followee_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(follower_id, followee_id)
    );

    CREATE TABLE IF NOT EXISTS hashtags (
        hashtag_id INTEGER PRIMARY KEY AUTOINCREMENT,
        hashtag_name VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS hashtag_follow (
        user_id INTEGER NOT NULL,
        hashtag_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(user_id, hashtag_id)
    );

    CREATE TABLE IF NOT EXISTS post_tags (
        post_id INTEGER NOT NULL,
        hashtag_id INTEGER NOT NULL,
        PRIMARY KEY(post_id, hashtag_id)
    );

    CREATE TABLE IF NOT EXISTS bookmarks (
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(user_id, post_id)
    );

    CREATE TABLE IF NOT EXISTS login (
        login_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ip VARCHAR(50) NOT NULL,
        login_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    '''
    cursor.executescript(schema_sqlite)
    conn.commit()

    order = [
        'users.sql',
        'photos.sql',
        'videos.sql',
        'post.sql',
        'comments.sql',
        'post_likes.sql',
        'comment_likes.sql',
        'follows.sql',
        'hashtags.sql',
        'hashtag_follow.sql',
        'post_tags.sql',
        'bookmarks.sql',
        'login.sql'
    ]

    base_dir = os.path.dirname(__file__)
    db_folder = os.path.join(base_dir, 'Database')

    for fname in order:
        fpath = os.path.join(db_folder, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        stmts = split_sql_statements(content)
        for s in stmts:
            s = s.strip()
            clean_lines = [l for l in s.splitlines() if not l.strip().startswith('--') and not l.strip().startswith('#')]
            s = '\n'.join(clean_lines).strip()
            if not s:
                continue
            s = re.sub(r'\bVALUE\b', 'VALUES', s, flags=re.IGNORECASE)
            if s.upper().startswith('INSERT INTO'):
                s = 'INSERT OR IGNORE INTO' + s[11:]
            try:
                cursor.execute(s)
            except Exception as e:
                pass

    conn.commit()
    conn.close()
    print("[DB] Initialization completed successfully.")
    return DB_PATH

if __name__ == '__main__':
    init_database(force=True)
