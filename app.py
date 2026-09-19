from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import init_db, get_db, seed_demo_data
from ai_insights import analyze_feedback, build_dashboard_insights

app = Flask(__name__)
app.config["SECRET_KEY"] = "localloop-hackathon-secret"

init_db()
seed_demo_data()

@app.route("/")
def index():
    db = get_db()
    business = db.execute("SELECT * FROM businesses LIMIT 1").fetchone()
    feedback = db.execute("""
        SELECT * FROM feedback
        WHERE business_id = ?
        ORDER BY created_at DESC
    """, (business["id"],)).fetchall()
    insights = build_dashboard_insights(feedback)
    return render_template("index.html", business=business, insights=insights)

@app.route("/dashboard")
def dashboard():
    db = get_db()
    business = db.execute("SELECT * FROM businesses LIMIT 1").fetchone()
    feedback = db.execute("""
        SELECT * FROM feedback
        WHERE business_id = ?
        ORDER BY created_at DESC
    """, (business["id"],)).fetchall()
    insights = build_dashboard_insights(feedback)
    return render_template("dashboard.html", business=business, feedback=feedback, insights=insights)

@app.route("/feedback")
def feedback_page():
    db = get_db()
    business = db.execute("SELECT * FROM businesses LIMIT 1").fetchone()
    return render_template("feedback.html", business=business)

@app.post("/feedback")
def submit_feedback():
    business_id = request.form.get("business_id", type=int)
    rating = request.form.get("rating", type=int)
    comment = request.form.get("comment", "").strip()

    if not business_id or not rating or not comment:
        flash("Please provide a rating and feedback.", "error")
        return redirect(url_for("feedback_page"))

    analysis = analyze_feedback(comment, rating)
    db = get_db()
    db.execute("""
        INSERT INTO feedback
        (business_id, rating, comment, sentiment, theme, urgency, ai_summary, action)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        business_id, rating, comment,
        analysis["sentiment"], analysis["theme"], analysis["urgency"],
        analysis["summary"], analysis["action"]
    ))
    db.commit()
    flash("Thanks! Your feedback was added to the business insight loop.", "success")
    return redirect(url_for("feedback_page"))

@app.post("/api/analyze")
def api_analyze():
    data = request.get_json(silent=True) or {}
    comment = (data.get("comment") or "").strip()
    rating = int(data.get("rating") or 3)
    if not comment:
        return jsonify({"error": "Comment is required"}), 400
    return jsonify(analyze_feedback(comment, rating))

@app.post("/api/business")
def create_business():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    category = (data.get("category") or "").strip()
    location = (data.get("location") or "").strip()

    if not name or not category:
        return jsonify({"error": "Name and category are required"}), 400

    db = get_db()
    db.execute("DELETE FROM businesses")
    cur = db.execute(
        "INSERT INTO businesses (name, category, location) VALUES (?, ?, ?)",
        (name, category, location)
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "message": "Business created"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
