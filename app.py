from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_database():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            data_per_day REAL NOT NULL,
            validity INTEGER NOT NULL,
            calls TEXT NOT NULL,
            sms TEXT NOT NULL,
            five_g INTEGER NOT NULL,
            ott TEXT NOT NULL
        )
    """)

    count = conn.execute(
        "SELECT COUNT(*) FROM plans"
    ).fetchone()[0]

    if count == 0:

        plans = [

            ("Basic 1GB", 199, 1, 28,
             "Unlimited", "100/day", 0, "None"),

            ("Smart 1.5GB", 299, 1.5, 28,
             "Unlimited", "100/day", 1, "None"),

            ("Power 2GB", 349, 2, 28,
             "Unlimited", "100/day", 1, "None"),

            ("Super 2.5GB", 399, 2.5, 28,
             "Unlimited", "100/day", 1, "JioCinema"),

            ("Max 3GB", 449, 3, 28,
             "Unlimited", "100/day", 1, "Disney+"),

            ("Long Validity", 599, 2, 56,
             "Unlimited", "100/day", 1, "None")
        ]

        conn.executemany("""
            INSERT INTO plans
            (name, price, data_per_day, validity,
             calls, sms, five_g, ott)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, plans)

    conn.commit()
    conn.close()


# ---------------- HOME ----------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------- RECOMMENDATION ----------------

@app.route("/recommend", methods=["POST"])
def recommend():

    user_type = request.form["user_type"]

    budget = float(request.form["budget"])

    data_required = float(
        request.form["data"]
    )

    validity_required = int(
        request.form["validity"]
    )

    five_g_required = (
        request.form.get("five_g") == "yes"
    )

    ott_required = (
        request.form.get("ott") == "yes"
    )

    conn = get_db()

    plans = conn.execute(
        "SELECT * FROM plans"
    ).fetchall()

    conn.close()

    recommendations = []

    for plan in plans:

        # Don't show plans above budget
        if plan["price"] > budget:
            continue

        score = 0
        reasons = []

        # ---------- DATA ----------
        if plan["data_per_day"] >= data_required:

            score += 35

            reasons.append(
                "Data requirement matched"
            )

        else:

            score += 10

            reasons.append(
                "Lower data than requested"
            )

        # ---------- BUDGET ----------
        if plan["price"] <= budget:

            score += 25

            reasons.append(
                "Within your budget"
            )

        # ---------- VALIDITY ----------
        if plan["validity"] >= validity_required:

            score += 15

            reasons.append(
                "Validity requirement matched"
            )

        # ---------- 5G ----------
        if five_g_required:

            if plan["five_g"] == 1:

                score += 15

                reasons.append(
                    "5G supported"
                )

        else:

            score += 15

        # ---------- OTT ----------
        if ott_required:

            if plan["ott"] != "None":

                score += 10

                reasons.append(
                    "Includes OTT benefit"
                )

        else:

            score += 10

        # ---------- USER TYPE BONUS ----------

        if user_type == "Gamer":

            if plan["data_per_day"] >= 2:

                score += 5

                reasons.append(
                    "Suitable for gaming usage"
                )

        elif user_type == "Streaming":

            if plan["data_per_day"] >= 2:

                score += 5

                reasons.append(
                    "Suitable for streaming"
                )

        elif user_type == "Student":

            if plan["price"] <= 399:

                score += 5

                reasons.append(
                    "Budget-friendly for students"
                )

        elif user_type == "Normal":

            if plan["price"] <= 399:

                score += 5

        recommendations.append({

            "plan": plan,

            "score": min(score, 100),

            "reasons": reasons

        })

    # Highest score first
    recommendations.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return render_template(
        "results.html",
        recommendations=recommendations,
        user_type=user_type
    )


# ---------------- RUN ----------------

if __name__ == "__main__":

    create_database()

    app.run(debug=True)