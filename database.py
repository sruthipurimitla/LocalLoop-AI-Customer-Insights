import sqlite3
from pathlib import Path
from flask import g

DB_PATH = Path(__file__).with_name("localloop.db")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS businesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        location TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        comment TEXT NOT NULL,
        sentiment TEXT NOT NULL,
        theme TEXT NOT NULL,
        urgency TEXT NOT NULL,
        ai_summary TEXT NOT NULL,
        action TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (business_id) REFERENCES businesses(id)
    );
    """)
    db.commit()
    db.close()

def seed_demo_data():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    existing = db.execute("SELECT COUNT(*) AS n FROM businesses").fetchone()["n"]
    if existing:
        db.close()
        return

    cur = db.execute(
        "INSERT INTO businesses (name, category, location) VALUES (?, ?, ?)",
        ("Bean & Bloom Café", "Café", "Kavali, Andhra Pradesh")
    )
    business_id = cur.lastrowid

    demo = [
        (5, "The coffee was amazing and the staff were very friendly.", "positive", "Product quality", "low",
         "Customers are praising product quality and staff friendliness.",
         "Protect the current quality and recognize the service team."),
        (2, "Food was good but the waiting time was too long during lunch.", "negative", "Waiting time", "high",
         "Long peak-hour waiting time is creating dissatisfaction.",
         "Test a faster peak-hour ordering workflow."),
        (4, "Loved the sandwich. Please add more vegetarian options.", "positive", "Product requests", "medium",
         "Customers like the food and are asking for more vegetarian choices.",
         "Consider testing two additional vegetarian items."),
        (3, "Prices feel slightly high compared with nearby cafés.", "neutral", "Pricing", "medium",
         "Pricing is creating some customer hesitation.",
         "Run a small pricing/value experiment before changing prices."),
        (2, "The order took 25 minutes and nobody explained the delay.", "negative", "Waiting time", "high",
         "Customers are frustrated by delays and poor delay communication.",
         "Add queue visibility and proactive delay updates."),
        (5, "Great atmosphere. I would definitely come back.", "positive", "Experience", "low",
         "The overall experience is encouraging repeat visits.",
         "Keep the ambience consistent and measure repeat visits."),
        (2, "Packaging leaked a little on my takeaway order.", "negative", "Packaging", "medium",
         "A packaging issue is affecting takeaway experience.",
         "Audit packaging for high-liquid items."),
        (4, "The new cold coffee is excellent.", "positive", "Product quality", "low",
         "The new product is receiving positive feedback.",
         "Track repeat purchases of the new product.")
    ]

    for rating, comment, sentiment, theme, urgency, summary, action in demo:
        db.execute("""
            INSERT INTO feedback
            (business_id, rating, comment, sentiment, theme, urgency, ai_summary, action)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (business_id, rating, comment, sentiment, theme, urgency, summary, action))

    db.commit()
    db.close()
