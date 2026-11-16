"""
Social Media Database Project - Full Stack Application Server
Zero-dependency multi-threaded HTTP server using Python standard library.
"""
import os
import sys
import json
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# In-memory session state for active user (default to user_id=1)
ACTIVE_USER_ID = 1

MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon'
}

class SocialMediaHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status_code=200):
        body = json.dumps(data, default=str).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status_code=400):
        self.send_json({"error": message, "success": False}, status_code=status_code)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def read_json_body(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                raw_data = self.rfile.read(content_length).decode('utf-8')
                return json.loads(raw_data) if raw_data else {}
            return {}
        except Exception:
            return {}

    def serve_file(self, file_path):
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        ext = os.path.splitext(file_path)[1].lower()
        content_type = MIME_TYPES.get(ext, 'application/octet-stream')

        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"500 Internal Error: {e}".encode('utf-8'))

    def do_GET(self):
        global ACTIVE_USER_ID
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        # Static assets
        if path == '/' or path == '/index.html':
            self.serve_file(os.path.join(STATIC_DIR, 'index.html'))
            return
        elif path.startswith('/static/'):
            rel_path = path[len('/static/'):]
            target_path = os.path.join(STATIC_DIR, rel_path)
            self.serve_file(target_path)
            return
        elif path in ('/ER Diagram.png', '/ER%20Diagram.png', '/er-diagram.png'):
            self.serve_file(os.path.join(BASE_DIR, 'ER Diagram.png'))
            return

        # API Endpoints
        if path == '/api/stats':
            stats = database.get_stats()
            self.send_json({"success": True, "stats": stats})
            return

        elif path == '/api/current-user':
            profile = database.get_user_profile(ACTIVE_USER_ID, ACTIVE_USER_ID)
            self.send_json({"success": True, "user": profile})
            return

        elif path == '/api/users':
            search = query_params.get('search', [''])[0]
            limit = int(query_params.get('limit', [60])[0])
            users = database.get_users(search=search, limit=limit)
            self.send_json({"success": True, "users": users})
            return

        elif path.startswith('/api/users/'):
            parts = path.split('/')
            if len(parts) >= 4 and parts[3].isdigit():
                user_id = int(parts[3])
                user = database.get_user_profile(user_id, ACTIVE_USER_ID)
                if not user:
                    self.send_error_json("User not found", 404)
                    return
                # Also fetch user's posts
                posts = database.get_feed(current_user_id=ACTIVE_USER_ID, user_id=user_id, limit=30)
                self.send_json({"success": True, "user": user, "posts": posts})
                return

        elif path == '/api/feed':
            filter_type = query_params.get('filter', ['all'])[0]
            search = query_params.get('search', [''])[0]
            tag = query_params.get('tag', [''])[0]
            user_id = int(query_params['user_id'][0]) if 'user_id' in query_params else None
            limit = int(query_params.get('limit', [20])[0])
            offset = int(query_params.get('offset', [0])[0])

            posts = database.get_feed(
                current_user_id=ACTIVE_USER_ID,
                filter_type=filter_type,
                search=search,
                tag=tag,
                user_id=user_id,
                limit=limit,
                offset=offset
            )
            self.send_json({"success": True, "posts": posts, "count": len(posts)})
            return

        elif path.startswith('/api/posts/') and path.endswith('/comments'):
            parts = path.split('/')
            if len(parts) >= 4 and parts[3].isdigit():
                post_id = int(parts[3])
                comments = database.get_post_comments(post_id, ACTIVE_USER_ID)
                self.send_json({"success": True, "comments": comments})
                return

        elif path == '/api/db/tables':
            tables = database.get_all_tables()
            self.send_json({"success": True, "tables": tables})
            return

        elif path.startswith('/api/db/table/'):
            parts = path.split('/')
            if len(parts) >= 5:
                table_name = parts[4]
                limit = int(query_params.get('limit', [100])[0])
                offset = int(query_params.get('offset', [0])[0])
                data = database.get_table_data(table_name, limit, offset)
                if data is None:
                    self.send_error_json("Table not found", 404)
                    return
                self.send_json({"success": True, **data})
                return

        elif path == '/api/hashtags':
            hashtags = database.get_hashtags()
            self.send_json({"success": True, "hashtags": hashtags})
            return

        elif path == '/api/analytics':
            queries = database.get_predefined_queries()
            stats = database.get_stats()
            self.send_json({"success": True, "stats": stats, "queries": queries})
            return

        else:
            self.send_error_json("Endpoint not found", 404)

    def do_POST(self):
        global ACTIVE_USER_ID
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        # Switch active user
        if path == '/api/current-user':
            user_id = body.get('user_id')
            if user_id:
                profile = database.get_user_profile(int(user_id), int(user_id))
                if profile:
                    ACTIVE_USER_ID = int(user_id)
                    self.send_json({"success": True, "user": profile})
                    return
            self.send_error_json("Invalid user ID", 400)
            return

        # Create post
        elif path == '/api/posts':
            caption = body.get('caption', '')
            location = body.get('location', '')
            photo_url = body.get('photo_url', '')
            video_url = body.get('video_url', '')
            tags = body.get('tags', [])
            user_id = body.get('user_id', ACTIVE_USER_ID)

            if not caption and not photo_url and not video_url:
                self.send_error_json("Post must have a caption or media.", 400)
                return

            try:
                new_post = database.create_post(
                    user_id=user_id,
                    caption=caption,
                    location=location,
                    photo_url=photo_url,
                    video_url=video_url,
                    tags=tags
                )
                self.send_json({"success": True, "post": new_post})
            except Exception as e:
                self.send_error_json(str(e), 500)
            return

        # Toggle like post
        elif path.startswith('/api/posts/') and path.endswith('/like'):
            parts = path.split('/')
            post_id = int(parts[3])
            user_id = body.get('user_id', ACTIVE_USER_ID)
            res = database.toggle_like_post(user_id, post_id)
            self.send_json({"success": True, **res})
            return

        # Toggle bookmark post
        elif path.startswith('/api/posts/') and path.endswith('/bookmark'):
            parts = path.split('/')
            post_id = int(parts[3])
            user_id = body.get('user_id', ACTIVE_USER_ID)
            res = database.toggle_bookmark(user_id, post_id)
            self.send_json({"success": True, **res})
            return

        # Add comment
        elif path.startswith('/api/posts/') and path.endswith('/comments'):
            parts = path.split('/')
            post_id = int(parts[3])
            user_id = body.get('user_id', ACTIVE_USER_ID)
            text = body.get('comment_text', '')
            try:
                comment = database.add_comment(user_id, post_id, text)
                self.send_json({"success": True, "comment": comment})
            except Exception as e:
                self.send_error_json(str(e), 400)
            return

        # Toggle comment like
        elif path.startswith('/api/comments/') and path.endswith('/like'):
            parts = path.split('/')
            comment_id = int(parts[3])
            user_id = body.get('user_id', ACTIVE_USER_ID)
            res = database.toggle_like_comment(user_id, comment_id)
            self.send_json({"success": True, **res})
            return

        # Toggle follow user
        elif path.startswith('/api/users/') and path.endswith('/follow'):
            parts = path.split('/')
            followee_id = int(parts[3])
            follower_id = body.get('user_id', ACTIVE_USER_ID)
            try:
                res = database.toggle_follow(follower_id, followee_id)
                self.send_json({"success": True, **res})
            except Exception as e:
                self.send_error_json(str(e), 400)
            return

        # Create user
        elif path == '/api/users':
            username = body.get('username')
            email = body.get('email')
            bio = body.get('bio', '')
            photo_url = body.get('profile_photo_url', '')
            if not username or not email:
                self.send_error_json("Username and email are required", 400)
                return
            try:
                new_user = database.create_user(username, email, bio, photo_url)
                self.send_json({"success": True, "user": new_user})
            except Exception as e:
                self.send_error_json(str(e), 400)
            return

        # Toggle follow hashtag
        elif path.startswith('/api/hashtags/') and path.endswith('/follow'):
            parts = path.split('/')
            hashtag_id = int(parts[3])
            user_id = body.get('user_id', ACTIVE_USER_ID)
            res = database.toggle_follow_hashtag(user_id, hashtag_id)
            self.send_json({"success": True, **res})
            return

        # Run specific predefined query
        elif path.startswith('/api/analytics/run/'):
            parts = path.split('/')
            qid = int(parts[4])
            queries = database.get_predefined_queries()
            target = next((q for q in queries if q['id'] == qid), None)
            if not target:
                self.send_error_json("Query not found", 404)
                return
            try:
                result = database.run_query(target['sql'])
                self.send_json({"success": True, "query": target, "result": result})
            except Exception as e:
                self.send_error_json(str(e), 500)
            return

        # Custom SQL query runner (read-only SELECT)
        elif path == '/api/query':
            sql = body.get('sql', '').strip()
            if not sql:
                self.send_error_json("SQL query cannot be empty", 400)
                return

            # Security sanity check for educational demo: allow only SELECT / EXPLAIN
            first_word = sql.split()[0].upper() if sql.split() else ''
            if first_word not in ('SELECT', 'EXPLAIN', 'PRAGMA', 'WITH'):
                self.send_error_json("Only SELECT / read-only queries are permitted in the interactive console.", 403)
                return

            try:
                result = database.run_query(sql)
                self.send_json({"success": True, "result": result})
            except Exception as e:
                self.send_error_json(str(e), 400)
            return

        else:
            self.send_error_json("Endpoint not found", 404)

    def log_message(self, format, *args):
        # Keep logs clean
        return

def run_server(port=5000):
    database.init_db()
    server_address = ('', port)
    try:
        httpd = ThreadingHTTPServer(server_address, SocialMediaHandler)
        print(f"=====================================================")
        print(f" Social Media Database Project is LIVE!")
        print(f" URL: http://localhost:{port}")
        print(f" Port: {port}")
        print(f" Database: {database.DB_PATH}")
        print(f"=====================================================")
        httpd.serve_forever()
    except OSError as e:
        if port < 5010:
            print(f"[Server] Port {port} in use, trying port {port + 1}...")
            run_server(port + 1)
        else:
            print(f"[Server] Could not bind port: {e}")

if __name__ == '__main__':
    port = 5000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
