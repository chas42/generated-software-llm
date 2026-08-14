import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify

# -----------------------------------------------------------------------------
# App Configuration
# -----------------------------------------------------------------------------

app = Flask(__name__)

DATABASE_NAME = "uptime_db"

# -----------------------------------------------------------------------------
# Database Initialization
# -----------------------------------------------------------------------------

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id TEXT NOT NULL,
            token TEXT NOT NULL,
            last_notification TEXT NOT NULL,
            UNIQUE(service_id, token)
        )
    """)

    conn.commit()
    conn.close()


init_db()

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    try:
        if not request.is_json:
            return jsonify({"error": "Invalid request payload"}), 400

        data = request.get_json()

        service_id = data.get("serviceId")
        token = data.get("token")

        if not service_id or not token:
            return jsonify({"error": "Invalid request payload"}), 400

        now = datetime.utcnow().isoformat()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert or update heartbeat
        cursor.execute("""
            INSERT INTO services (service_id, token, last_notification)
            VALUES (?, ?, ?)
            ON CONFLICT(service_id, token)
            DO UPDATE SET last_notification=excluded.last_notification
        """, (service_id, token, now))

        conn.commit()
        conn.close()

        return jsonify({"message": "Heartbeat registered successfully."}), 200

    except Exception:
        return jsonify({"error": "Internal server error"}), 500


@app.route("/services", methods=["POST"])
def get_services():
    try:
        if not request.is_json:
            return jsonify({"error": "Invalid request payload"}), 400

        data = request.get_json()
        token = data.get("token")

        if not token:
            return jsonify({"error": "Invalid request payload"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT service_id, last_notification
            FROM services
            WHERE token = ?
        """, (token,))

        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            result.append({
                "serviceId": row["service_id"],
                "lastNotification": row["last_notification"]
            })

        return jsonify(result), 200

    except Exception:
        return jsonify({"error": "Internal server error"}), 500


# -----------------------------------------------------------------------------
# Run Server
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)