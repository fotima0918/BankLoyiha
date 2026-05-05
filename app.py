from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import pyodbc
from config import get_connection_string

app = Flask(__name__)
app.secret_key = "super_secret_key"  # Required for session


def get_db_connection():
    """Azure SQL bazasiga ulanish"""
    conn = pyodbc.connect(get_connection_string())
    return conn


def row_to_dict(cursor, row):
    """Pyodbc row ni dict ga aylantirish"""
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def rows_to_list(cursor, rows):
    """Barcha rowlarni list of dict ga aylantirish"""
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


# Views
@app.route("/")
def index():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    # Simple hardcoded authentication
    if username == "fotima" and password == "12345":
        session["logged_in"] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Login yoki parol xato"})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("index"))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    customers_count = cursor.execute("SELECT COUNT(*) FROM Customers").fetchone()[0]
    total_balance = cursor.execute("SELECT ISNULL(SUM(Balance), 0) FROM Customers").fetchone()[0]
    males = cursor.execute("SELECT COUNT(*) FROM Customers WHERE Gender='Erkak'").fetchone()[0]
    females = cursor.execute("SELECT COUNT(*) FROM Customers WHERE Gender='Ayol'").fetchone()[0]
    conn.close()
    
    stats = {
        "customers_count": customers_count,
        "total_balance": total_balance,
        "males": males,
        "females": females
    }
    
    return render_template("dashboard.html", stats=stats)


@app.route("/customers")
def customers():
    if not session.get("logged_in"):
        return redirect(url_for("index"))
    return render_template("customers.html")


# APIs
@app.route("/api/customers")
def api_customers():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Customers")
    customers = rows_to_list(cursor, cursor.fetchall())
    conn.close()
    
    return jsonify(customers)


@app.route("/api/history")
def api_history():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT h.Id, sender.FullName as SenderName, receiver.FullName as ReceiverName, h.Amount, h.Date 
        FROM History h
        JOIN Customers sender ON h.SenderId = sender.Id
        JOIN Customers receiver ON h.ReceiverId = receiver.Id
        ORDER BY h.Date DESC
    ''')
    history = rows_to_list(cursor, cursor.fetchall())
    conn.close()
    
    # Date ni string ga aylantirish
    for h in history:
        if h.get("Date"):
            h["Date"] = str(h["Date"])
    
    return jsonify(history)


@app.route("/api/transfer", methods=["POST"])
def api_transfer():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    sender_id = data.get("from")
    receiver_id = data.get("to")
    amount = data.get("amount")
    
    try:
        amount = int(amount)
        if amount <= 0:
            return jsonify({"message": "Summa noldan katta bo'lishi kerak"}), 400
    except (ValueError, TypeError):
        return jsonify({"message": "Noto'g'ri summa"}), 400
        
    if sender_id == receiver_id:
        return jsonify({"message": "O'ziga pul o'tkazish mumkin emas"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM Customers WHERE Id = ?", (sender_id,))
    sender = cursor.fetchone()
    cursor.execute("SELECT * FROM Customers WHERE Id = ?", (receiver_id,))
    receiver = cursor.fetchone()
    
    if not sender or not receiver:
        conn.close()
        return jsonify({"message": "ID noto'g'ri"}), 400
    
    # sender[3] = Balance (index 3)
    sender_dict = row_to_dict(cursor, sender) if hasattr(cursor, 'description') else None
    # Re-fetch to get proper dict
    cursor.execute("SELECT Balance FROM Customers WHERE Id = ?", (sender_id,))
    sender_balance = cursor.fetchone()[0]
    
    if sender_balance < amount:
        conn.close()
        return jsonify({"message": "Pul yetarli emas"}), 400
        
    # Transaction
    try:
        cursor.execute("UPDATE Customers SET Balance = Balance - ? WHERE Id = ?", (amount, sender_id))
        cursor.execute("UPDATE Customers SET Balance = Balance + ? WHERE Id = ?", (amount, receiver_id))
        cursor.execute("INSERT INTO History (SenderId, ReceiverId, Amount) VALUES (?, ?, ?)", (sender_id, receiver_id, amount))
        conn.commit()
        success = True
    except Exception as e:
        conn.rollback()
        success = False
    finally:
        conn.close()
        
    if success:
        return jsonify({"message": "Transfer muvaffaqiyatli ✔", "success": True})
    else:
        return jsonify({"message": "Transferda xatolik yuz berdi", "success": False}), 500


@app.route("/api/customers", methods=["POST"])
def api_add_customer():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    full_name = data.get("full_name", "").strip()
    gender = data.get("gender", "").strip()
    balance = data.get("balance", 0)
    
    if not full_name or not gender:
        return jsonify({"success": False, "message": "Ism va jinsi to'ldirilishi shart"}), 400
    
    try:
        balance = int(balance)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Noto'g'ri balans"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Customers (FullName, Gender, Balance) VALUES (?, ?, ?)",
                   (full_name, gender, balance))
    conn.commit()
    # Azure SQL da lastrowid olish
    cursor.execute("SELECT SCOPE_IDENTITY()")
    new_id = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({"success": True, "message": "Mijoz muvaffaqiyatli qo'shildi ✔", "id": new_id})


@app.route("/api/customers/<int:customer_id>", methods=["PUT"])
def api_edit_customer(customer_id):
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    full_name = data.get("full_name", "").strip()
    gender = data.get("gender", "").strip()
    balance = data.get("balance", 0)
    
    if not full_name or not gender:
        return jsonify({"success": False, "message": "Ism va jinsi to'ldirilishi shart"}), 400
    
    try:
        balance = int(balance)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Noto'g'ri balans"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Customers WHERE Id = ?", (customer_id,))
    customer = cursor.fetchone()
    if not customer:
        conn.close()
        return jsonify({"success": False, "message": "Mijoz topilmadi"}), 404
    
    cursor.execute("UPDATE Customers SET FullName = ?, Gender = ?, Balance = ? WHERE Id = ?",
                 (full_name, gender, balance, customer_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Mijoz muvaffaqiyatli tahrirlandi ✔"})


@app.route("/api/customers/<int:customer_id>", methods=["DELETE"])
def api_delete_customer(customer_id):
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Customers WHERE Id = ?", (customer_id,))
    customer = cursor.fetchone()
    if not customer:
        conn.close()
        return jsonify({"success": False, "message": "Mijoz topilmadi"}), 404
    
    cursor.execute("DELETE FROM Customers WHERE Id = ?", (customer_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Mijoz o'chirildi ✔"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
