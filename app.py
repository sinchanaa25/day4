from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# MYSQL CONFIG
app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST")
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER")
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.getenv("MYSQL_DB")
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# INIT DB
def init_db():
    cur = mysql.connection.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            equipment_id INT AUTO_INCREMENT PRIMARY KEY,
            equipment_name VARCHAR(100),
            serial_number VARCHAR(50) UNIQUE,
            department VARCHAR(100),
            purchase_date DATE,
            status VARCHAR(50)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_log (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            equipment_id INT,
            maintenance_date DATE,
            technician_name VARCHAR(100),
            issue_reported TEXT,
            resolution_notes TEXT,
            next_due_date DATE,
            FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
        )
    """)

    mysql.connection.commit()
    cur.close()

with app.app_context():
    init_db()

# DASHBOARD
@app.route("/")
def dashboard():
    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM equipment")
    total = cur.fetchone()['total']

    cur.execute("SELECT status, COUNT(*) AS count FROM equipment GROUP BY status")
    status_data = cur.fetchall()

    cur.execute("""
        SELECT e.equipment_name, m.next_due_date
        FROM equipment e
        JOIN maintenance_log m ON e.equipment_id = m.equipment_id
        WHERE m.next_due_date < CURDATE()
    """)
    overdue = cur.fetchall()

    cur.close()

    return render_template("dashboard.html",
                           total=total,
                           status_data=status_data,
                           overdue=overdue)

# EQUIPMENT LIST
@app.route("/equipment")
def equipment_list():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM equipment")
    equipment = cur.fetchall()
    cur.close()

    return render_template("equipment_list.html", equipment=equipment)

# ADD EQUIPMENT
@app.route("/add-equipment", methods=["GET", "POST"])
def add_equipment():
    if request.method == "POST":
        data = request.form
        cur = mysql.connection.cursor()

        cur.execute("""
            INSERT INTO equipment (equipment_name, serial_number, department, purchase_date, status)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            data["name"],
            data["serial"],
            data["department"],
            data["purchase_date"],
            "Active"
        ))

        mysql.connection.commit()
        cur.close()
        return redirect(url_for("equipment_list"))

    return render_template("add_equipment.html")

# EQUIPMENT DETAIL
@app.route("/equipment/<int:id>")
def equipment_detail(id):
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM equipment WHERE equipment_id=%s", (id,))
    equipment = cur.fetchone()

    cur.execute("SELECT * FROM maintenance_log WHERE equipment_id=%s", (id,))
    logs = cur.fetchall()

    cur.close()

    return render_template("equipment_detail.html",
                           equipment=equipment,
                           logs=logs)

# ADD MAINTENANCE
@app.route("/equipment/<int:id>/add-maintenance", methods=["GET", "POST"])
def add_maintenance(id):
    if request.method == "POST":
        data = request.form
        cur = mysql.connection.cursor()

        cur.execute("""
            INSERT INTO maintenance_log
            (equipment_id, maintenance_date, technician_name, issue_reported, resolution_notes, next_due_date)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            id,
            data["maintenance_date"],
            data["technician_name"],
            data["issue"],
            data["resolution"],
            data["next_due_date"]
        ))

        mysql.connection.commit()
        cur.close()

        return redirect(url_for("equipment_detail", id=id))

    return render_template("add_maintenance.html", id=id)

if __name__ == "__main__":
    app.run(debug=True)