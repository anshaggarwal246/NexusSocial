"""
Database abstraction layer for Social Media Database Project.
Handles SQLite connection, seed data loading, and all CRUD + analytical operations.
"""
import sqlite3
import os
import re
import time

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

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.create_function(
        "REGEXP", 2,
        lambda expr, item: bool(re.search(expr, item, re.IGNORECASE)) if item else False
    )
    return conn

def init_db(force=False):
    if os.path.exists(DB_PATH) and not force:
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM post")
            count = cur.fetchone()[0]
            conn.close()
            if count > 0:
                return
        except Exception:
            pass

    print("[Database] Initializing database and importing seeds...")
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    conn = get_connection()
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
            except Exception:
                pass

    conn.commit()
    conn.close()
    print("[Database] Initialized social_media.db with complete records.")

# --- API Methods ---

def get_stats():
    conn = get_connection()
    cur = conn.cursor()
    stats = {}
    for table in ['users', 'post', 'comments', 'post_likes', 'comment_likes', 'follows', 'hashtags', 'bookmarks']:
        cur.execute(f"SELECT count(*) FROM {table}")
        stats[table] = cur.fetchone()[0]
    conn.close()
    return stats

def get_users(search='', limit=60):
    conn = get_connection()
    cur = conn.cursor()
    if search:
        cur.execute("""
            SELECT u.*, 
                (SELECT count(*) FROM follows WHERE followee_id = u.user_id) AS follower_count,
                (SELECT count(*) FROM follows WHERE follower_id = u.user_id) AS following_count,
                (SELECT count(*) FROM post WHERE user_id = u.user_id) AS post_count
            FROM users u
            WHERE u.username LIKE ? OR u.bio LIKE ? OR u.email LIKE ?
            ORDER BY follower_count DESC
            LIMIT ?
        """, (f'%{search}%', f'%{search}%', f'%{search}%', limit))
    else:
        cur.execute("""
            SELECT u.*, 
                (SELECT count(*) FROM follows WHERE followee_id = u.user_id) AS follower_count,
                (SELECT count(*) FROM follows WHERE follower_id = u.user_id) AS following_count,
                (SELECT count(*) FROM post WHERE user_id = u.user_id) AS post_count
            FROM users u
            ORDER BY follower_count DESC
            LIMIT ?
        """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_user_profile(user_id, current_user_id=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.*, 
            (SELECT count(*) FROM follows WHERE followee_id = u.user_id) AS follower_count,
            (SELECT count(*) FROM follows WHERE follower_id = u.user_id) AS following_count,
            (SELECT count(*) FROM post WHERE user_id = u.user_id) AS post_count
        FROM users u
        WHERE u.user_id = ?
    """, (user_id,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return None
    user_dict = dict(user)

    is_following = False
    if current_user_id:
        cur.execute("SELECT 1 FROM follows WHERE follower_id = ? AND followee_id = ?", (current_user_id, user_id))
        is_following = cur.fetchone() is not None
    user_dict['is_following'] = is_following

    conn.close()
    return user_dict

def get_feed(current_user_id=1, filter_type='all', search='', tag='', user_id=None, limit=20, offset=0):
    conn = get_connection()
    cur = conn.cursor()

    where_clauses = []
    params = []

    if user_id:
        where_clauses.append("p.user_id = ?")
        params.append(user_id)

    if tag:
        tag_clean = tag.strip().lstrip('#')
        where_clauses.append("p.post_id IN (SELECT pt.post_id FROM post_tags pt JOIN hashtags h ON h.hashtag_id = pt.hashtag_id WHERE LOWER(TRIM(REPLACE(h.hashtag_name, '#', ''))) = LOWER(?))")
        params.append(tag_clean)

    if search:
        search_term = f"%{search.strip()}%"
        where_clauses.append("(p.caption LIKE ? OR p.location LIKE ? OR u.username LIKE ?)")
        params.extend([search_term, search_term, search_term])

    if filter_type == 'photos':
        where_clauses.append("ph.photo_url IS NOT NULL")
    elif filter_type == 'videos':
        where_clauses.append("vd.video_url IS NOT NULL")
    elif filter_type == 'bookmarks' and current_user_id:
        where_clauses.append("p.post_id IN (SELECT post_id FROM bookmarks WHERE user_id = ?)")
        params.append(current_user_id)

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    order_by = "ORDER BY p.post_id DESC"
    if filter_type == 'trending':
        order_by = "ORDER BY likes_count DESC, comments_count DESC"

    query = f"""
    SELECT 
        p.post_id,
        p.caption,
        p.location,
        p.created_at,
        p.user_id,
        u.username,
        u.profile_photo_url,
        ph.photo_url,
        vd.video_url,
        (SELECT COUNT(*) FROM post_likes pl WHERE pl.post_id = p.post_id) AS likes_count,
        (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.post_id) AS comments_count,
        (SELECT COUNT(*) FROM bookmarks b WHERE b.post_id = p.post_id) AS bookmarks_count,
        CASE WHEN EXISTS (SELECT 1 FROM post_likes pl WHERE pl.post_id = p.post_id AND pl.user_id = ?) THEN 1 ELSE 0 END AS has_liked,
        CASE WHEN EXISTS (SELECT 1 FROM bookmarks b WHERE b.post_id = p.post_id AND b.user_id = ?) THEN 1 ELSE 0 END AS has_bookmarked
    FROM post p
    JOIN users u ON u.user_id = p.user_id
    LEFT JOIN photos ph ON ph.photo_id = p.photo_id
    LEFT JOIN videos vd ON vd.video_id = p.video_id
    {where_sql}
    {order_by}
    LIMIT ? OFFSET ?
    """
    exec_params = [current_user_id or 0, current_user_id or 0] + params + [limit, offset]
    cur.execute(query, exec_params)
    posts = [dict(r) for r in cur.fetchall()]

    # Fetch hashtags for each post
    for post in posts:
        cur.execute("""
            SELECT h.hashtag_id, TRIM(h.hashtag_name) as hashtag_name
            FROM post_tags pt
            JOIN hashtags h ON h.hashtag_id = pt.hashtag_id
            WHERE pt.post_id = ?
        """, (post['post_id'],))
        post['tags'] = [dict(t) for t in cur.fetchall()]

    conn.close()
    return posts

def get_post_comments(post_id, current_user_id=1):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            c.comment_id,
            c.comment_text,
            c.created_at,
            c.user_id,
            u.username,
            u.profile_photo_url,
            (SELECT COUNT(*) FROM comment_likes cl WHERE cl.comment_id = c.comment_id) AS likes_count,
            CASE WHEN EXISTS (SELECT 1 FROM comment_likes cl WHERE cl.comment_id = c.comment_id AND cl.user_id = ?) THEN 1 ELSE 0 END AS has_liked
        FROM comments c
        JOIN users u ON u.user_id = c.user_id
        WHERE c.post_id = ?
        ORDER BY c.comment_id ASC
    """, (current_user_id or 0, post_id))
    comments = [dict(r) for r in cur.fetchall()]
    conn.close()
    return comments

def toggle_like_post(user_id, post_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM post_likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
    exists = cur.fetchone() is not None

    if exists:
        cur.execute("DELETE FROM post_likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        liked = False
    else:
        cur.execute("INSERT INTO post_likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        liked = True
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM post_likes WHERE post_id = ?", (post_id,))
    count = cur.fetchone()[0]
    conn.close()
    return {"liked": liked, "likes_count": count}

def toggle_bookmark(user_id, post_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM bookmarks WHERE user_id = ? AND post_id = ?", (user_id, post_id))
    exists = cur.fetchone() is not None

    if exists:
        cur.execute("DELETE FROM bookmarks WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        bookmarked = False
    else:
        cur.execute("INSERT INTO bookmarks (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
        bookmarked = True
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM bookmarks WHERE post_id = ?", (post_id,))
    count = cur.fetchone()[0]
    conn.close()
    return {"bookmarked": bookmarked, "bookmarks_count": count}

def add_comment(user_id, post_id, comment_text):
    if not comment_text or not comment_text.strip():
        raise ValueError("Comment text cannot be empty.")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO comments (user_id, post_id, comment_text) VALUES (?, ?, ?)",
                (user_id, post_id, comment_text.strip()))
    comment_id = cur.lastrowid
    conn.commit()

    cur.execute("""
        SELECT c.comment_id, c.comment_text, c.created_at, c.user_id, u.username, u.profile_photo_url,
               0 as likes_count, 0 as has_liked
        FROM comments c
        JOIN users u ON u.user_id = c.user_id
        WHERE c.comment_id = ?
    """, (comment_id,))
    new_comment = dict(cur.fetchone())
    conn.close()
    return new_comment

def toggle_like_comment(user_id, comment_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM comment_likes WHERE user_id = ? AND comment_id = ?", (user_id, comment_id))
    exists = cur.fetchone() is not None

    if exists:
        cur.execute("DELETE FROM comment_likes WHERE user_id = ? AND comment_id = ?", (user_id, comment_id))
        liked = False
    else:
        cur.execute("INSERT INTO comment_likes (user_id, comment_id) VALUES (?, ?)", (user_id, comment_id))
        liked = True
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM comment_likes WHERE comment_id = ?", (comment_id,))
    count = cur.fetchone()[0]
    conn.close()
    return {"liked": liked, "likes_count": count}

def toggle_follow(follower_id, followee_id):
    if follower_id == followee_id:
        raise ValueError("Cannot follow yourself.")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM follows WHERE follower_id = ? AND followee_id = ?", (follower_id, followee_id))
    exists = cur.fetchone() is not None

    if exists:
        cur.execute("DELETE FROM follows WHERE follower_id = ? AND followee_id = ?", (follower_id, followee_id))
        following = False
    else:
        cur.execute("INSERT INTO follows (follower_id, followee_id) VALUES (?, ?)", (follower_id, followee_id))
        following = True
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM follows WHERE followee_id = ?", (followee_id,))
    count = cur.fetchone()[0]
    conn.close()
    return {"following": following, "follower_count": count}

def create_post(user_id, caption, location="", photo_url=None, video_url=None, tags=None):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO post (user_id, caption, location) VALUES (?, ?, ?)",
                (user_id, caption, location or "Earth"))
    post_id = cur.lastrowid

    photo_id = None
    if photo_url and photo_url.strip():
        cur.execute("INSERT INTO photos (photo_url, post_id, size) VALUES (?, ?, 2.0)",
                    (photo_url.strip(), post_id))
        photo_id = cur.lastrowid
        cur.execute("UPDATE post SET photo_id = ? WHERE post_id = ?", (photo_id, post_id))

    video_id = None
    if video_url and video_url.strip():
        cur.execute("INSERT INTO videos (video_url, post_id, size) VALUES (?, ?, 4.0)",
                    (video_url.strip(), post_id))
        video_id = cur.lastrowid
        cur.execute("UPDATE post SET video_id = ? WHERE post_id = ?", (video_id, post_id))

    if tags:
        for t in tags:
            t = t.strip()
            if not t:
                continue
            if not t.startswith("#"):
                t = "#" + t
            cur.execute("SELECT hashtag_id FROM hashtags WHERE LOWER(TRIM(hashtag_name)) = LOWER(?)", (t,))
            row = cur.fetchone()
            if row:
                hid = row[0]
            else:
                cur.execute("INSERT INTO hashtags (hashtag_name) VALUES (?)", (t,))
                hid = cur.lastrowid
            cur.execute("INSERT OR IGNORE INTO post_tags (post_id, hashtag_id) VALUES (?, ?)", (post_id, hid))

    conn.commit()
    conn.close()
    return get_feed(current_user_id=user_id, user_id=user_id, limit=1)[0]

def create_user(username, email, bio="", profile_photo_url=""):
    conn = get_connection()
    cur = conn.cursor()
    if not profile_photo_url:
        profile_photo_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}"
    cur.execute("""
        INSERT INTO users (username, email, bio, profile_photo_url)
        VALUES (?, ?, ?, ?)
    """, (username.strip(), email.strip(), bio.strip(), profile_photo_url.strip()))
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return get_user_profile(user_id)

def get_hashtags():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            h.hashtag_id,
            TRIM(h.hashtag_name) AS hashtag_name,
            (SELECT COUNT(*) FROM post_tags pt WHERE pt.hashtag_id = h.hashtag_id) AS post_count,
            (SELECT COUNT(*) FROM hashtag_follow hf WHERE hf.hashtag_id = h.hashtag_id) AS follow_count
        FROM hashtags h
        ORDER BY post_count DESC, follow_count DESC
    """)
    tags = [dict(r) for r in cur.fetchall()]
    conn.close()
    return tags

def toggle_follow_hashtag(user_id, hashtag_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM hashtag_follow WHERE user_id = ? AND hashtag_id = ?", (user_id, hashtag_id))
    exists = cur.fetchone() is not None

    if exists:
        cur.execute("DELETE FROM hashtag_follow WHERE user_id = ? AND hashtag_id = ?", (user_id, hashtag_id))
        following = False
    else:
        cur.execute("INSERT INTO hashtag_follow (user_id, hashtag_id) VALUES (?, ?)", (user_id, hashtag_id))
        following = True
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM hashtag_follow WHERE hashtag_id = ?", (hashtag_id,))
    count = cur.fetchone()[0]
    conn.close()
    return {"following": following, "follow_count": count}

# --- Analytical Queries from queries.sql ---

PREDEFINED_QUERIES = [
    {
        "id": 1,
        "title": "Location of User Posts",
        "description": "Finds all posts located in Agra, Maharashtra, or West Bengal.",
        "sql": """SELECT post_id, user_id, caption, location, created_at 
FROM post 
WHERE LOWER(location) IN ('agra', 'maharashtra', 'west bengal') 
ORDER BY post_id ASC;"""
    },
    {
        "id": 2,
        "title": "Most Followed Hashtags",
        "description": "Identifies the top 5 hashtags with the highest number of followers.",
        "sql": """SELECT 
    TRIM(h.hashtag_name) AS 'Hashtags', 
    COUNT(hf.hashtag_id) AS 'Total Follows' 
FROM hashtag_follow hf
JOIN hashtags h ON h.hashtag_id = hf.hashtag_id
GROUP BY hf.hashtag_id
ORDER BY COUNT(hf.hashtag_id) DESC 
LIMIT 5;"""
    },
    {
        "id": 3,
        "title": "Most Used / Trending Hashtags",
        "description": "Displays the top 10 most tagged hashtags across all posts.",
        "sql": """SELECT 
    TRIM(h.hashtag_name) AS 'Trending Hashtags', 
    COUNT(pt.hashtag_id) AS 'Times Used'
FROM hashtags h
JOIN post_tags pt ON h.hashtag_id = pt.hashtag_id
GROUP BY pt.hashtag_id
ORDER BY COUNT(pt.hashtag_id) DESC 
LIMIT 10;"""
    },
    {
        "id": 4,
        "title": "Most Inactive Users",
        "description": "Lists all registered users who have never posted anything.",
        "sql": """SELECT user_id, username AS 'Inactive User', email, created_at
FROM users
WHERE user_id NOT IN (SELECT DISTINCT user_id FROM post)
ORDER BY user_id ASC;"""
    },
    {
        "id": 5,
        "title": "Most Liked Posts",
        "description": "Ranks posts by total number of likes received.",
        "sql": """SELECT 
    p.post_id, 
    u.username AS 'Author', 
    p.caption, 
    p.location, 
    COUNT(pl.post_id) AS 'Like Count'
FROM post_likes pl
JOIN post p ON p.post_id = pl.post_id
JOIN users u ON u.user_id = p.user_id
GROUP BY pl.post_id
ORDER BY COUNT(pl.post_id) DESC 
LIMIT 10;"""
    },
    {
        "id": 6,
        "title": "Average Posts Per User",
        "description": "Calculates the platform-wide average posts per active user.",
        "sql": """SELECT 
    COUNT(post_id) AS 'Total Posts',
    COUNT(DISTINCT user_id) AS 'Active Creators',
    ROUND((COUNT(post_id) * 1.0 / COUNT(DISTINCT user_id)), 2) AS 'Average Post per User' 
FROM post;"""
    },
    {
        "id": 7,
        "title": "User Login Activity",
        "description": "Shows user accounts along with their recorded login frequencies and IPs.",
        "sql": """SELECT 
    u.user_id, 
    u.username, 
    u.email, 
    COUNT(l.login_id) AS 'Total Logins'
FROM users u
LEFT JOIN login l ON u.user_id = l.user_id
GROUP BY u.user_id
ORDER BY 'Total Logins' DESC
LIMIT 15;"""
    },
    {
        "id": 8,
        "title": "Bot Detection: Liked Every Single Post",
        "description": "Detects automated accounts that have liked 100% of the posts on the platform.",
        "sql": """SELECT u.username, COUNT(*) AS num_likes 
FROM users u
INNER JOIN post_likes pl ON u.user_id = pl.user_id 
GROUP BY pl.user_id 
HAVING num_likes = (SELECT COUNT(*) FROM post);"""
    },
    {
        "id": 9,
        "title": "Users Who Never Commented",
        "description": "Finds users who have never left a comment on any post.",
        "sql": """SELECT user_id, username AS 'User Never Comment', email, bio
FROM users
WHERE user_id NOT IN (SELECT DISTINCT user_id FROM comments)
ORDER BY user_id ASC;"""
    },
    {
        "id": 10,
        "title": "Bot Detection: Commented on Every Post",
        "description": "Detects bot accounts that have commented on every single post.",
        "sql": """SELECT u.username, COUNT(*) AS num_comment 
FROM users u
INNER JOIN comments c ON u.user_id = c.user_id 
GROUP BY c.user_id 
HAVING num_comment = (SELECT COUNT(*) FROM post);"""
    },
    {
        "id": 11,
        "title": "Users Not Followed by Anyone",
        "description": "Identifies users who currently have 0 followers.",
        "sql": """SELECT user_id, username AS 'Zero Followers', email, bio
FROM users
WHERE user_id NOT IN (SELECT DISTINCT followee_id FROM follows)
ORDER BY user_id ASC;"""
    },
    {
        "id": 12,
        "title": "Users Not Following Anyone",
        "description": "Identifies users who are not following any other user.",
        "sql": """SELECT user_id, username AS 'Following Nobody', email, bio
FROM users
WHERE user_id NOT IN (SELECT DISTINCT follower_id FROM follows)
ORDER BY user_id ASC;"""
    },
    {
        "id": 13,
        "title": "Super Creators (Posted > 5 Times)",
        "description": "Finds the most prolific creators who have published more than 5 posts.",
        "sql": """SELECT 
    u.user_id, 
    u.username, 
    COUNT(p.user_id) AS post_count 
FROM post p
JOIN users u ON u.user_id = p.user_id
GROUP BY p.user_id
HAVING post_count > 5
ORDER BY post_count DESC;"""
    },
    {
        "id": 14,
        "title": "Top Influencers (Followers > 40)",
        "description": "Lists accounts that have amassed more than 40 followers.",
        "sql": """SELECT 
    u.user_id, 
    u.username, 
    COUNT(f.follower_id) AS follower_count 
FROM follows f
JOIN users u ON u.user_id = f.followee_id
GROUP BY f.followee_id
HAVING follower_count > 40
ORDER BY follower_count DESC;"""
    },
    {
        "id": 15,
        "title": "Sentiment Filter: Praise in Comments",
        "description": "Searches for positive sentiment keywords like 'good' or 'beautiful' in comments.",
        "sql": """SELECT 
    c.comment_id, 
    u.username AS 'Commenter', 
    c.comment_text, 
    c.post_id 
FROM comments c
JOIN users u ON u.user_id = c.user_id
WHERE c.comment_text REGEXP 'good|beautiful'
ORDER BY c.comment_id ASC
LIMIT 15;"""
    },
    {
        "id": 16,
        "title": "Longest Post Captions",
        "description": "Finds the 5 posts with the longest captions written by users.",
        "sql": """SELECT 
    p.post_id, 
    u.username, 
    p.caption, 
    LENGTH(p.caption) AS caption_length,
    p.location
FROM post p
JOIN users u ON u.user_id = p.user_id
ORDER BY caption_length DESC 
LIMIT 5;"""
    }
]

def run_query(sql_string):
    start = time.time()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql_string)
    columns = [desc[0] for desc in cur.description] if cur.description else []
    rows = [dict(zip(columns, row)) for row in cur.fetchall()]
    elapsed_ms = round((time.time() - start) * 1000, 2)
    conn.close()
    return {
        "columns": columns,
        "rows": rows,
        "count": len(rows),
        "execution_time_ms": elapsed_ms
    }

def get_all_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    result = []
    for t in tables:
        cur.execute(f"SELECT count(*) FROM {t}")
        cnt = cur.fetchone()[0]
        result.append({"table_name": t, "row_count": cnt})
    conn.close()
    return result

def get_table_data(table_name, limit=100, offset=0):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cur.fetchone():
        conn.close()
        return None
    cur.execute(f"SELECT count(*) FROM {table_name}")
    total_count = cur.fetchone()[0]
    cur.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET ?", (limit, offset))
    columns = [desc[0] for desc in cur.description] if cur.description else []
    rows = [dict(zip(columns, row)) for row in cur.fetchall()]
    conn.close()
    return {
        "table_name": table_name,
        "columns": columns,
        "rows": rows,
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }

def get_predefined_queries():
    return PREDEFINED_QUERIES
