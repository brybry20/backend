from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlite3 import Error
from db import get_conn, init_db

app = Flask(__name__)
CORS(app)  # allow requests from frontend/dev server

# ✅ GET all transactions
@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    data = [dict(r) for r in rows]
    return jsonify(data), 200


# ✅ DELETE transaction
@app.route("/api/transactions/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Transaction deleted"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ✅ ADD new transaction (with parking slot validation)
@app.route("/api/transactions", methods=["POST"])
def add_transaction():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    # Basic validation
    if not data.get("owner_name") or not data.get("plate_number"):
        return jsonify({"error": "owner_name and plate_number are required"}), 400
    if not data.get("parking_slot"):
        return jsonify({"error": "parking_slot is required"}), 400

    try:
        conn = get_conn()
        cur = conn.cursor()

        # ✅ Check if parking slot is already occupied (no exit_time)
        cur.execute("""
            SELECT * FROM transactions
            WHERE parking_slot = ? AND exit_time IS NULL
        """, (data["parking_slot"],))
        existing = cur.fetchone()
        if existing:
            conn.close()
            return jsonify({"error": "Parking slot already occupied."}), 400

        # ✅ Insert new transaction
        cur.execute("""
            INSERT INTO transactions
            (owner_name, vehicle_name, vehicle_type, plate_number, entry_time, exit_time, parking_slot)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("owner_name"),
            data.get("vehicle_name"),
            data.get("vehicle_type"),
            data.get("plate_number"),
            data.get("entry_time"),
            data.get("exit_time"),
            data.get("parking_slot"),
        ))
        conn.commit()

        new_id = cur.lastrowid
        cur.execute("SELECT * FROM transactions WHERE id = ?", (new_id,))
        new_row = cur.fetchone()
        conn.close()

        return jsonify(dict(new_row)), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ✅ UPDATE transaction
@app.route("/api/transactions/<int:id>", methods=["PUT"])
def update_transaction(id):
    data = request.get_json()
    exit_time = data.get("exit_time")

    conn = get_conn()
    cur = conn.cursor()

    # ✅ Fetch the transaction first
    cur.execute("SELECT * FROM transactions WHERE id = ?", (id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Transaction not found"}), 404

    # ✅ If exit_time is being updated, move to history
    if exit_time:
        cur.execute("""
            INSERT INTO history (owner_name, vehicle_name, vehicle_type, plate_number, entry_time, exit_time, parking_slot)
            SELECT owner_name, vehicle_name, vehicle_type, plate_number, entry_time, ?, parking_slot
            FROM transactions WHERE id = ?
        """, (exit_time, id))

        # ✅ Delete from transactions table
        cur.execute("DELETE FROM transactions WHERE id = ?", (id,))

        # ✅ Free the parking slot (optional if you have a parking table)
        conn.commit()
        conn.close()
        return jsonify({"message": "Transaction moved to history"}), 200

    # ✅ If just updating something else
    cur.execute("UPDATE transactions SET exit_time = ? WHERE id = ?", (exit_time, id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Transaction updated"}), 200


# ✅ Get occupied parking slots
@app.route("/api/parking/occupied", methods=["GET"])
def get_occupied_slots():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT parking_slot FROM transactions
            WHERE exit_time IS NULL AND parking_slot IS NOT NULL
        """)
        rows = cur.fetchall()
        conn.close()
        return jsonify([r["parking_slot"] for r in rows]), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/history", methods=["GET"])
def get_history():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY id DESC")
    rows = cur.fetchall()

    history = [
        {
            "id": r[0],
            "owner_name": r[1],
            "vehicle_name": r[2],
            "vehicle_type": r[3],
            "plate_number": r[4],
            "entry_time": r[5],
            "exit_time": r[6],
            "parking_slot": r[7]
        }
        for r in rows
    ]

    conn.close()
    return jsonify(history)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
