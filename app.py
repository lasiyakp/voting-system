"""Flask Voting System."""

import os
import sqlite3
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from model.decision_tree import predict_candidate

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "voting.db"

app = Flask(__name__)
app.secret_key = "dummy-secret-key"  # Dummy key for demo only


# ---------------------------
# Database helper functions
# ---------------------------
def get_db():
    """Get a single DB connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Close DB connection after each request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Initialize application tables and baseline state."""
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            age INTEGER DEFAULT 25,
            gender TEXT DEFAULT 'M',
            prev_vote TEXT DEFAULT 'A'
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            party TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS votes (
            user_id INTEGER UNIQUE NOT NULL,
            candidate_id INTEGER NOT NULL,
            voted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )

    # Seed only the required admin account (no demo users/candidates)
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        admin_user = (
            os.environ.get("DEFAULT_ADMIN_USERNAME", "admin"),
            os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin123"),
            "admin",
            35,
            "M",
            "A",
        )
        cur.execute(
            "INSERT INTO users(username, password, role, age, gender, prev_vote) VALUES(?,?,?,?,?,?)",
            admin_user,
        )

    cur.execute("SELECT 1 FROM app_state WHERE key = 'election_status'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO app_state(key, value) VALUES('election_status', 'open')"
        )

    db.commit()
    db.close()


# ---------------------------
# Utility functions
# ---------------------------
def current_user():
    """Fetch current logged in user from session."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_election_status(db):
    """Read election status from persistent app state."""
    row = db.execute(
        "SELECT value FROM app_state WHERE key = 'election_status'"
    ).fetchone()
    return row["value"] if row else "open"


def login_required(role=None):
    """Simple route-guard decorator-like helper."""

    def wrapper(fn):
        def inner(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Please log in first.", "warning")
                return redirect(url_for("login"))
            if role and user["role"] != role:
                flash("Access denied.", "danger")
                return redirect(url_for("dashboard"))
            return fn(*args, **kwargs)

        inner.__name__ = fn.__name__
        return inner

    return wrapper


# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Dummy login with role-based redirect."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()

        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            flash("Login successful!", "success")
            if user["role"] == "admin":
                return redirect(url_for("admin"))
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required(role="user")
def dashboard():
    """User dashboard with statistics and ML prediction."""
    db = get_db()
    user = current_user()

    candidates = db.execute("SELECT * FROM candidates ORDER BY id").fetchall()
    total_votes = db.execute("SELECT COUNT(*) AS c FROM votes").fetchone()["c"]

    vote_rows = db.execute(
        """
        SELECT c.name, COUNT(v.candidate_id) AS vote_count
        FROM candidates c
        LEFT JOIN votes v ON c.id = v.candidate_id
        GROUP BY c.id
        ORDER BY c.id
        """
    ).fetchall()

    user_vote = db.execute(
        "SELECT candidate_id FROM votes WHERE user_id = ?", (user["id"],)
    ).fetchone()
    election_status = get_election_status(db)

    # Decision-tree based prediction
    ml_prediction = predict_candidate(user["age"], user["gender"], user["prev_vote"])

    return render_template(
        "dashboard.html",
        user=user,
        candidates=candidates,
        total_votes=total_votes,
        vote_rows=vote_rows,
        has_voted=bool(user_vote),
        election_status=election_status,
        ml_prediction=ml_prediction,
    )


@app.route("/vote", methods=["GET", "POST"])
@login_required(role="user")
def vote():
    """Voting page that prevents duplicate vote per user."""
    db = get_db()
    user = current_user()
    election_status = get_election_status(db)

    if election_status != "open":
        flash("Voting is currently closed by the admin.", "warning")
        return redirect(url_for("dashboard"))

    has_voted = db.execute(
        "SELECT 1 FROM votes WHERE user_id = ?", (user["id"],)
    ).fetchone()
    if has_voted:
        flash("You have already voted. Duplicate voting is not allowed.", "warning")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        candidate_id = request.form.get("candidate_id")
        if not candidate_id:
            flash("Please select a candidate.", "danger")
            return redirect(url_for("vote"))

        candidate_exists = db.execute(
            "SELECT 1 FROM candidates WHERE id = ?",
            (int(candidate_id),),
        ).fetchone()
        if not candidate_exists:
            flash("Selected candidate no longer exists.", "danger")
            return redirect(url_for("vote"))

        db.execute(
            "INSERT INTO votes(user_id, candidate_id) VALUES(?, ?)",
            (user["id"], int(candidate_id)),
        )
        db.commit()

        flash("Your vote has been submitted successfully!", "success")
        return redirect(url_for("results"))

    candidates = db.execute("SELECT * FROM candidates ORDER BY id").fetchall()
    return render_template("vote.html", candidates=candidates)


@app.route("/results")
@login_required()
def results():
    """Live results page."""
    db = get_db()
    rows = db.execute(
        """
        SELECT c.id, c.name, c.party, COUNT(v.candidate_id) AS vote_count
        FROM candidates c
        LEFT JOIN votes v ON c.id = v.candidate_id
        GROUP BY c.id
        ORDER BY vote_count DESC, c.id ASC
        """
    ).fetchall()

    total_votes = db.execute("SELECT COUNT(*) AS c FROM votes").fetchone()["c"]
    return render_template("results.html", rows=rows, total_votes=total_votes)


@app.route("/admin", methods=["GET", "POST"])
@login_required(role="admin")
def admin():
    """Admin dashboard: manage candidates and view data."""
    db = get_db()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add_candidate":
            name = request.form.get("name", "").strip()
            party = request.form.get("party", "").strip()
            if name and party:
                db.execute("INSERT INTO candidates(name, party) VALUES(?, ?)", (name, party))
                db.commit()
                flash("Candidate added.", "success")
            else:
                flash("Candidate name and party are required.", "danger")

        elif action == "delete_candidate":
            candidate_id = request.form.get("candidate_id")
            # Remove votes first to keep data consistent
            db.execute("DELETE FROM votes WHERE candidate_id = ?", (candidate_id,))
            db.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
            db.commit()
            flash("Candidate deleted (and related votes removed).", "warning")

        elif action == "reset_voting":
            db.execute("DELETE FROM votes")
            db.commit()
            flash("Voting system reset: all votes cleared.", "info")

        elif action == "set_election_state":
            election_status = request.form.get("election_status", "").strip().lower()
            if election_status in {"open", "closed"}:
                db.execute(
                    "UPDATE app_state SET value = ? WHERE key = 'election_status'",
                    (election_status,),
                )
                db.commit()
                flash(f"Election state updated to: {election_status}.", "success")
            else:
                flash("Invalid election state.", "danger")

        return redirect(url_for("admin"))

    election_status = get_election_status(db)
    candidates = db.execute("SELECT * FROM candidates ORDER BY id").fetchall()
    users = db.execute("SELECT id, username, role, age, gender, prev_vote FROM users").fetchall()
    votes = db.execute(
        """
        SELECT u.username, c.name AS candidate_name, v.voted_at
        FROM votes v
        JOIN users u ON u.id = v.user_id
        JOIN candidates c ON c.id = v.candidate_id
        ORDER BY v.voted_at DESC
        """
    ).fetchall()

    return render_template(
        "admin.html",
        candidates=candidates,
        users=users,
        votes=votes,
        election_status=election_status,
    )


init_db()

if __name__ == "__main__":
    app.run(debug=True)
