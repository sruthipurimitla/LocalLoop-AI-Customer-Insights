import re
from collections import Counter

POSITIVE = {
    "amazing", "great", "good", "excellent", "love", "loved", "friendly",
    "helpful", "beautiful", "perfect", "fast", "fresh", "nice", "enjoyed"
}

NEGATIVE = {
    "bad", "poor", "slow", "late", "delay", "delayed", "long", "leak",
    "leaked", "expensive", "high", "terrible", "worst", "difficult",
    "frustrated", "wait", "waiting", "problem", "problems", "disappointed",
    "disappointing", "unhappy", "issue", "issues"
}

THEMES = {
    "Waiting time": [
        "wait", "waiting", "slow", "delay", "delayed", "minutes", "queue"
    ],
    "Pricing": [
        "price", "pricing", "expensive", "cost", "cheap", "value"
    ],
    "Product quality": [
        "food", "coffee", "quality", "taste", "fresh", "sandwich",
        "drink"
    ],
    "Service": [
        "staff", "service", "explained", "friendly", "helpful"
    ],
    "Packaging": [
        "packaging", "package", "leak", "leaked", "takeaway"
    ],
    "Product requests": [
        "add", "more", "option", "options", "vegetarian", "new"
    ],
    "Experience": [
        "atmosphere", "ambience", "experience", "return", "come back"
    ]
}


def words(text):
    return re.findall(r"[a-zA-Z']+", text.lower())


def analyze_feedback(comment, rating=3):
    text = comment.lower()
    ws = set(words(comment))

    positive_words = ws & POSITIVE
    negative_words = ws & NEGATIVE

    pos = len(positive_words)
    neg = len(negative_words)

    # Detect the main customer theme first.
    scores = {
        theme: sum(1 for key in keys if key in text)
        for theme, keys in THEMES.items()
    }

    theme = max(scores, key=scores.get)

    if scores[theme] == 0:
        theme = "General feedback"

    # Written feedback is more important than rating when
    # the customer explicitly reports a problem.
    complaint_detected = neg > 0

    if neg > pos:
        sentiment = "negative"
    elif pos > neg:
        sentiment = "positive"
    else:
        # Rating is used only when the written feedback is unclear.
        if rating >= 4:
            sentiment = "positive"
        elif rating <= 2:
            sentiment = "negative"
        else:
            sentiment = "neutral"

    # A specific recurring problem can be high priority even when
    # the overall rating is good.
    if theme == "Waiting time" and complaint_detected:
        urgency = "high"
    elif sentiment == "negative" and (rating <= 2 or complaint_detected):
        urgency = "high"
    elif complaint_detected:
        urgency = "medium"
    elif sentiment == "neutral":
        urgency = "medium"
    else:
        urgency = "low"

    summary = make_summary(
        sentiment,
        theme,
        comment,
        rating,
        complaint_detected
    )

    action = make_action(theme, sentiment)

    return {
        "sentiment": sentiment,
        "theme": theme,
        "urgency": urgency,
        "summary": summary,
        "action": action
    }


def make_summary(
    sentiment,
    theme,
    comment,
    rating,
    complaint_detected
):
    if complaint_detected and theme != "General feedback":
        return (
            f"Customer feedback highlights an issue with "
            f"{theme.lower()}, despite a {rating}/5 rating."
        )

    if sentiment == "negative":
        return (
            f"Customer dissatisfaction is mainly related to "
            f"{theme.lower()}."
        )

    if sentiment == "positive":
        return (
            f"Customer feedback is positive, with "
            f"{theme.lower()} standing out."
        )

    return (
        f"Customer feedback is mixed and points to "
        f"{theme.lower()} as an area to monitor."
    )


def make_action(theme, sentiment):
    actions = {
        "Waiting time": (
            "Test a faster peak-hour workflow and measure "
            "average service time."
        ),
        "Pricing": (
            "Run a small pricing/value experiment before "
            "making a permanent change."
        ),
        "Product quality": (
            "Protect the current quality and monitor "
            "repeat-purchase signals."
        ),
        "Service": (
            "Review service interactions and add a simple "
            "service-quality check."
        ),
        "Packaging": (
            "Audit packaging for affected products and "
            "test an improved option."
        ),
        "Product requests": (
            "Group requests by frequency and test the "
            "most requested item."
        ),
        "Experience": (
            "Preserve the strong experience and measure "
            "repeat visits."
        ),
        "General feedback": (
            "Review this feedback alongside similar "
            "comments before acting."
        )
    }

    return actions.get(theme, actions["General feedback"])


def build_dashboard_insights(feedback):
    rows = [dict(x) for x in feedback]
    total = len(rows)

    if total == 0:
        return {
            "total": 0,
            "avg_rating": 0,
            "positive_pct": 0,
            "negative_pct": 0,
            "themes": [],
            "priority": [],
            "recommendations": [],
            "recommended": {
                "theme": "Collect more feedback",
                "action": (
                    "Start collecting customer feedback "
                    "to generate insights."
                ),
                "impact": "—",
                "reason": (
                    "More customer feedback is needed before "
                    "prioritizing an issue."
                )
            }
        }

    avg = round(
        sum(r["rating"] for r in rows) / total,
        1
    )

    positive_pct = round(
        sum(r["sentiment"] == "positive" for r in rows)
        / total * 100
    )

    negative_pct = round(
        sum(r["sentiment"] == "negative" for r in rows)
        / total * 100
    )

    theme_counter = Counter(
        r["theme"] for r in rows
    )

    themes = [
        {
            "name": k,
            "count": v
        }
        for k, v in theme_counter.most_common()
    ]

    priority = []

    for theme, count in theme_counter.items():

        matching = [
            r for r in rows
            if r["theme"] == theme
        ]

        high = sum(
            r["urgency"] == "high"
            for r in matching
        )

        negative = sum(
            r["sentiment"] == "negative"
            for r in matching
        )

        # High urgency carries the greatest weight.
        # Negative feedback is next, followed by frequency.
        score = (
            (high * 4)
            + (negative * 2)
            + count
        )

        impact = (
            "High"
            if high >= 1
            else (
                "Medium"
                if negative >= 1 or count >= 2
                else "Low"
            )
        )

        priority.append({
            "theme": theme,
            "mentions": count,
            "high": high,
            "negative": negative,
            "score": score,
            "impact": impact,
            "action": matching[0]["action"]
        })

    priority.sort(
        key=lambda p: p["score"],
        reverse=True
    )

    recommendations = [
        p["action"]
        for p in priority[:3]
    ]

    top = priority[0] if priority else None

    recommended = {
        "theme": (
            top["theme"]
            if top
            else "Collect more feedback"
        ),
        "action": (
            top["action"]
            if top
            else (
                "Start collecting customer feedback "
                "to generate insights."
            )
        ),
        "impact": (
            top["impact"]
            if top
            else "—"
        ),
        "reason": (
            f"{top['high']} high-urgency mention(s) and "
            f"{top['negative']} negative mention(s) make "
            f"this the most important issue to investigate."
            if top
            else (
                "More customer feedback is needed before "
                "prioritizing an issue."
            )
        )
    }

    return {
        "total": total,
        "avg_rating": avg,
        "positive_pct": positive_pct,
        "negative_pct": negative_pct,
        "themes": themes,
        "priority": priority,
        "recommendations": recommendations,
        "recommended": recommended
    }