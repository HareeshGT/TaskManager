from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ✅ Absolute DB path (IMPORTANT FIX)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

# ---------------- DB CONNECTION ----------------
def get_db():
    return sqlite3.connect(DB_PATH)

# ---------------- DB INIT ----------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    print("Using DB at:", DB_PATH)  # debug

    # Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    # Tasks table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT NOT NULL,
            completed INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE user_id=?", (session['user_id'],))
    tasks = cur.fetchall()
    conn.close()

    return render_template('index.html', tasks=tasks)

# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = generate_password_hash(request.form['password'])

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return "User already exists"

        conn.close()
        return redirect('/login')

    return render_template('signup.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            return redirect('/')
        else:
            return "Invalid credentials"

    return render_template('login.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- ADD TASK ----------------
@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect('/login')

    task = request.form['content']
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (user_id, content) VALUES (?, ?)",
        (session['user_id'], task)
    )
    conn.commit()
    conn.close()

    return redirect('/')

# ---------------- DELETE ----------------
@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM tasks WHERE id=? AND user_id=?",
        (id, session['user_id'])   # ✅ SECURITY FIX
    )
    conn.commit()
    conn.close()

    return redirect('/')

# ---------------- COMPLETE ----------------
@app.route('/complete/<int:id>')
def complete(id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET completed=1 WHERE id=? AND user_id=?",
        (id, session['user_id'])   # ✅ SECURITY FIX
    )
    conn.commit()
    conn.close()

    return redirect('/')


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))