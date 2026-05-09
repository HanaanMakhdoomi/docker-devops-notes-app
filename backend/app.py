from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import time

app = Flask(__name__)
CORS(app)

def get_db_connection():
    while True:
        try:
            database_url = os.getenv("postgresql://notes_db_jk4u_user:vm0eoReOmJTvIgX2S7VKQJ9qdh6eURCf@dpg-d7voinjbc2fs73d204gg-a/notes_db_jk4u")

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
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            title TEXT DEFAULT 'Untitled',
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
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

@app.route("/")
def home():
    return "Backend is running!"

@app.route("/notes", methods=["GET"])
def get_notes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, content, created_at 
        FROM notes 
        ORDER BY id DESC;
    """)
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
def add_note():
    data = request.get_json()
    title = data.get("title", "Untitled")
    content = data.get("content")

    if not content:
        return jsonify({"error": "Note content is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO notes (title, content) VALUES (%s, %s) RETURNING id, created_at;",
        (title, content)
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
def delete_note(note_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE id = %s;", (note_id,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Note deleted"})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
