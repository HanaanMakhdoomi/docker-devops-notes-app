from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import os
import time
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

def get_db_connection():
    while True:
        try:
            database_url = os.getenv("DATABASE_URL")

            if database_url:
                return psycopg2.connect(database_url)

            return psycopg2.connect(
                host=os.getenv("DB_HOST", "db"),
                database=os.getenv("DB_NAME", "notesdb"),
                user=os.getenv("DB_USER", "admin"),
                password=os.getenv("DB_PASSWORD", "password")
            )
        except psycopg2.OperationalError:
            print("Database not ready, retrying in 2 seconds...")
            time.sleep(2)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            title TEXT DEFAULT 'Untitled',
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("""
        ALTER TABLE notes 
        ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
    """)

    cur.execute("""
        ALTER TABLE notes 
        ADD COLUMN IF NOT EXISTS title TEXT DEFAULT 'Untitled';
    """)

    cur.execute("""
        ALTER TABLE notes 
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    """)

    conn.commit()
    cur.close()
    conn.close()

def create_token(user_id, username):
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_id = data["user_id"]
            request.username = data["username"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated

@app.route("/")
def home():
    return "Backend is running!"

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    password_hash = generate_password_hash(password)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id;",
            (username, password_hash)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": "Username already exists"}), 409

    cur.close()
    conn.close()

    token = create_token(user_id, username)

    return jsonify({
        "message": "Signup successful",
        "token": token,
        "username": username
    }), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, username, password_hash FROM users WHERE username = %s;",
        (username,)
    )
    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        return jsonify({"error": "Invalid username or password"}), 401

    user_id, db_username, password_hash = user

    if not check_password_hash(password_hash, password):
        return jsonify({"error": "Invalid username or password"}), 401

    token = create_token(user_id, db_username)

    return jsonify({
        "message": "Login successful",
        "token": token,
        "username": db_username
    })

@app.route("/notes", methods=["GET"])
@token_required
def get_notes():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, content, created_at 
        FROM notes 
        WHERE user_id = %s
        ORDER BY id DESC;
    """, (request.user_id,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    notes = [
        {
            "id": row[0],
            "title": row[1] or "Untitled",
            "content": row[2],
            "created_at": row[3].isoformat() if row[3] else None
        }
        for row in rows
    ]

    return jsonify(notes)

@app.route("/notes", methods=["POST"])
@token_required
def add_note():
    data = request.get_json()
    title = data.get("title", "Untitled")
    content = data.get("content", "").strip()

    if not content:
        return jsonify({"error": "Note content is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO notes (user_id, title, content) 
        VALUES (%s, %s, %s) 
        RETURNING id, created_at;
        """,
        (request.user_id, title, content)
    )

    note_id, created_at = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "id": note_id,
        "title": title,
        "content": content,
        "created_at": created_at.isoformat()
    }), 201

@app.route("/notes/<int:note_id>", methods=["DELETE"])
@token_required
def delete_note(note_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM notes WHERE id = %s AND user_id = %s;",
        (note_id, request.user_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Note deleted"})

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
