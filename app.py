from flask import Flask, render_template, request, redirect, url_for
import sqlite3, os
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = "static/images"
DB_NAME = "database.db"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------- Инициализация базы --------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS screenshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_path TEXT,
        date TEXT,
        created_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS trade_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        screenshot_id INTEGER,
        instrument TEXT,
        gap TEXT,
        bar1 TEXT,
        bar2 TEXT,
        structure TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -------------------- Главная страница --------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("screenshot")
        date = request.form.get("date")
        instrument = request.form.get("Instrument")
        gap = request.form.get("Gap")
        bar1 = request.form.get("1 Bar")
        bar2 = request.form.get("2 Bar")
        structure = request.form.get("2 Bar Structure")

        if file:
            filename = datetime.now().strftime("%Y%m%d%H%M%S") + ".png"
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)

            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()

            c.execute("INSERT INTO screenshots (image_path, date, created_at) VALUES (?, ?, ?)",
                      (path, date, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            screenshot_id = c.lastrowid

            c.execute("""
            INSERT INTO trade_data (screenshot_id, instrument, gap, bar1, bar2, structure)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (screenshot_id, instrument, gap, bar1, bar2, structure))

            conn.commit()
            conn.close()

        return redirect(url_for("index"))

    return render_template("add.html")

# -------------------- Статистика --------------------
@app.route("/stats", methods=["GET", "POST"])
def stats():
    results = []
    total = 0
    percentage = 0

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if request.method == "POST":
        instrument = request.form.get("Instrument")
        gap = request.form.get("Gap")
        bar1 = request.form.get("1 Bar")
        bar2 = request.form.get("2 Bar")
        structure = request.form.get("2 Bar Structure")

        query = """
        SELECT s.date, s.image_path
        FROM screenshots s
        JOIN trade_data t ON s.id = t.screenshot_id
        WHERE instrument=? AND gap=? AND bar1=? AND bar2=? AND structure=?
        """
        c.execute(query, (instrument, gap, bar1, bar2, structure))
        rows = c.fetchall()

        # создаём список словарей с датой и именем файла
        results = [{"date": r[0], "filename": os.path.basename(r[1])} for r in rows]

        c.execute("SELECT COUNT(*) FROM screenshots")
        total_screens = c.fetchone()[0]

        total = len(results)
        percentage = (total / total_screens * 100) if total_screens else 0

    conn.close()

    return render_template("stats.html", results=results, total=total, percentage=percentage)

# -------------------- Просмотр всех сделок --------------------
@app.route("/trades")
def trades():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT s.id, s.image_path, s.date, t.instrument, t.gap, t.bar1, t.bar2, t.structure
    FROM screenshots s
    JOIN trade_data t ON s.id = t.screenshot_id
    ORDER BY s.id DESC
    """)
    trades = c.fetchall()
    conn.close()

    return render_template("trades.html", trades=trades)

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)