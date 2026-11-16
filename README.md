# Social Media Database & Web Application

A full-stack social media application and interactive DBMS analytics dashboard built on the SQL schema and data from the **Social Media Database Project**.

---

## 🚀 Quick Start (How to Run)

### Method 1: One-Click Runner (Windows)
Double-click the included batch script:
```cmd
run.bat
```
This automatically starts the local web server and opens the frontend in your default browser at **`http://localhost:5000`**.

---

### Method 2: Command Line (Windows, macOS, Linux)
Ensure you have **Python 3.8+** installed (no pip packages required — built purely with standard library modules):

```bash
# 1. Run the application
python app.py

# Or specify a custom port:
python app.py 8080
```

Open your browser and navigate to:
```
http://localhost:5000
```

---

## ✨ Features & Capabilities

### 1. Modern Social Feed
- **Interactive Posts**: View posts with creator information, location badges, photos, and embedded YouTube videos.
- **Micro-Interactions**: Double-tap photos or click the heart button to like with animation; toggle bookmarks; copy share links.
- **Live Comments**: Expand comments on any post, like individual comments, and publish new comments instantly.
- **Smart Filtering**: Filter by **All**, **Photos Only**, **Videos Only**, **Top Liked (Trending)**, or **Saved Bookmarks**.
- **Real-time Search**: Search across post captions, locations, creators, and `#hashtags`.

### 2. Multi-Persona User Switcher
- Switch active user identity seamlessly from the top navigation bar between any of the **50 registered database users** (e.g., `kanavphull`, `Sahib Singh`, `Sakshi Warandani`).
- Experience following, liking, and bookmarking as different users in real-time.

### 3. Creator Explorer & Profile Modals
- View all 50 accounts with follower/following counts, biographies, and post counters.
- Follow / Unfollow creators with immediate database persistence.
- Click any user to view their detailed profile modal and gallery of published posts.
- Register new user accounts via modal dialog.

### 4. Trending Hashtags & Topics
- Explore all 31 platform hashtags with real-time post usage counts and follower stats.
- Follow hashtags or click any tag to filter feed posts immediately.

### 5. DBMS Analytics & Benchmark Dashboard (16 Queries)
- **1-Click Execution**: Interactive runner for all **16 core DBMS queries** from `queries.sql`.
- **Query Inspector**: View formatted SQL syntax, query execution time in milliseconds (`⚡ <1ms`), and dynamic tabular results.
- **Benchmark All**: One-click benchmark runner to measure sequential performance across all analytical queries.
- Predefined queries include:
  1. *Location of User Posts*
  2. *Most Followed Hashtags*
  3. *Trending / Most Used Hashtags*
  4. *Most Inactive Users*
  5. *Most Liked Posts*
  6. *Average Posts per User*
  7. *User Login Frequency & IPs*
  8. *Bot Detection: Users who liked every post*
  9. *Users Who Never Commented*
  10. *Bot Detection: Users who commented on every post*
  11. *Users with Zero Followers*
  12. *Users Following Nobody*
  13. *Super Creators (Posted > 5 times)*
  14. *Top Influencers (Followers > 40)*
  15. *Sentiment Filter: Praise in Comments*
  16. *Longest Post Captions*

### 6. Interactive SQL Console
- Direct read-only SQL querying playground.
- Type custom `SELECT` statements against `social_media.db` with shortcut presets and `Ctrl+Enter` execution.

### 7. Entity Relationship (ER) Diagram Viewer
- View the full-resolution relational ER Diagram mapping tables (`users`, `post`, `photos`, `videos`, `comments`, `post_likes`, `comment_likes`, `follows`, `hashtags`, `hashtag_follow`, `post_tags`, `bookmarks`, `login`).

---

## 🗄️ Database Statistics

The database comes pre-seeded with over **4,500+ records**:
- **50** Registered Users
- **100** Posts
- **199** Comments
- **1,707** Post Likes
- **381** Comment Likes
- **1,873** Follow Relationships
- **31** Hashtags
- **377** Post-Hashtag associations
- **194** Bookmarks
- **100** Login Records

---

## 📁 Project Architecture

```
Social-Media-Database-Project/
│
├── app.py                 # Application launcher
├── server.py              # Multi-threaded HTTP server & REST API
├── database.py            # SQLite database layer & 16 analytical queries
├── init_db.py             # Database seed importer & migration script
├── run.bat                # Windows 1-click startup launcher
│
├── static/                # Modern Frontend SPA
│   ├── index.html         # Semantic HTML5 layout
│   ├── style.css          # Dark/Light responsive UI styling
│   ├── app.js             # Client-side reactivity, feeds, & SQL console
│   └── er_diagram.png     # High-resolution ER diagram
│
├── Database/              # Original SQL seed files
│   ├── users.sql
│   ├── post.sql
│   ├── photos.sql
│   ├── videos.sql
│   ├── comments.sql
│   ├── follows.sql
│   └── ...
│
├── schema.sql             # SQL Schema definition
├── table_database.sql     # Full database SQL script
├── queries.sql            # 16 Analytical queries
└── ER Diagram.png         # Database Entity Relationship diagram
```

---

## 👩‍💻👨‍💻 Original Authors & Team
- [Kanav Phull](https://github.com/kanavphull)
- [Raj Gupta](https://github.com/RAJGUPTA28)
- [Sahib Singh](https://github.com/ssahibsingh)
- [Sakshi Warandani](https://github.com/Sa960)
