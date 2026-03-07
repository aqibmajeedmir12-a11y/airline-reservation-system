"""
SkyFlow Flask Backend
Main application file with all routes and database integration
"""

import os
from datetime import datetime, timedelta, timezone
from functools import wraps
import jwt
from flask import Flask, request, send_from_directory, g
from flask_cors import CORS
import sqlite3
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ===== CONFIG =====
SECRET_KEY = "skyflow-secret-key-2024"
DB_PATH = os.path.join(os.path.dirname(__file__), "skyflow.db")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
app.config['SECRET_KEY'] = SECRET_KEY
CORS(app)

# ===== EMAIL CONFIG =====
EMAIL_SENDER = "aqibmajeedmir12@gmail.com"
EMAIL_PASSWORD = ""  # Set your Gmail App Password here
EMAIL_ENABLED = False  # Set to True once you add an App Password

def send_booking_email(to_email, passenger_name, booking_id, flight_id, from_city, to_city, dep_time, arr_time, travel_date, fare, seat, meal, payment):
    """Send a professional booking confirmation email"""
    if not EMAIL_ENABLED or not EMAIL_PASSWORD:
        print(f"[EMAIL] Skipped (not configured). Would send to {to_email}")
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f'SkyFlow Airlines <{EMAIL_SENDER}>'
        msg['To'] = to_email
        msg['Subject'] = f'✈ Booking Confirmed - {booking_id} | SkyFlow Airlines'

        html = f"""
        <html>
        <body style="margin:0;padding:0;background:#04091e;font-family:Arial,sans-serif;">
          <div style="max-width:600px;margin:40px auto;background:#071235;border-radius:16px;overflow:hidden;border:1px solid rgba(0,201,255,0.2);">
            <div style="background:linear-gradient(135deg,#00c9ff,#7b2ff7);padding:32px 28px;text-align:center;">
              <h1 style="margin:0;color:#fff;font-size:28px;">✈ SkyFlow Airlines</h1>
              <p style="margin:8px 0 0;color:rgba(255,255,255,0.9);font-size:14px;">Booking Confirmation</p>
            </div>
            <div style="padding:28px;">
              <p style="color:#a0aec0;font-size:14px;margin:0 0 20px;">Dear <strong style="color:#fff;">{passenger_name}</strong>,</p>
              <p style="color:#a0aec0;font-size:14px;margin:0 0 24px;">Congratulations! 🎉 Your flight has been booked successfully. Here are your booking details:</p>
              <div style="background:rgba(0,201,255,0.08);border:1px solid rgba(0,201,255,0.2);border-radius:12px;padding:20px;margin-bottom:24px;">
                <table style="width:100%;border-collapse:collapse;">
                  <tr><td style="color:#a0aec0;padding:6px 0;font-size:13px;">Booking ID</td><td style="color:#00c9ff;font-weight:bold;text-align:right;padding:6px 0;">{booking_id}</td></tr>
                  <tr><td style="color:#a0aec0;padding:6px 0;font-size:13px;">Flight</td><td style="color:#fff;font-weight:bold;text-align:right;padding:6px 0;">{flight_id}</td></tr>
                  <tr><td style="color:#a0aec0;padding:6px 0;font-size:13px;">Route</td><td style="color:#fff;font-weight:bold;text-align:right;padding:6px 0;">{from_city} → {to_city}</td></tr>
                  <tr><td style="color:#a0aec0;padding:6px 0;font-size:13px;">Date</td><td style="color:#fff;text-align:right;padding:6px 0;">{travel_date}</td></tr>
                  <tr><td style="color:#a0aec0;padding:6px 0;font-size:13px;">Departure</td><td style="color:#fff;text-align:right;padding:6px 0;">{dep_time}</td></tr>
                  <tr><td style="color:#a0aec0;padding:6px 0;font-size:13px;">Arrival</td><td style="color:#fff;text-align:right;padding:6px 0;">{arr_time}</td></tr>
                  <tr><td style="color:#a0aec0;padding:6px 0;font-size:13px;">Seat</td><td style="color:#fff;text-align:right;padding:6px 0;">{seat}</td></tr>
                  <tr><td style="color:#a0aec0;padding:6px 0;font-size:13px;">Meal</td><td style="color:#fff;text-align:right;padding:6px 0;">{meal}</td></tr>
                  <tr><td style="color:#a0aec0;padding:6px 0;font-size:13px;">Payment</td><td style="color:#fff;text-align:right;padding:6px 0;">{payment}</td></tr>
                  <tr style="border-top:1px solid rgba(0,201,255,0.15);"><td style="color:#a0aec0;padding:12px 0 6px;font-size:13px;">Total Fare</td><td style="color:#00c9ff;font-size:20px;font-weight:bold;text-align:right;padding:12px 0 6px;">Rs.{int(fare):,}</td></tr>
                </table>
              </div>
              <p style="color:#a0aec0;font-size:13px;margin:0 0 12px;">Please arrive at the airport at least 2 hours before departure. Carry a valid government-issued photo ID.</p>
              <p style="color:#a0aec0;font-size:13px;margin:0;">We wish you a safe and pleasant journey!</p>
            </div>
            <div style="background:rgba(0,0,0,0.3);padding:16px 28px;text-align:center;">
              <p style="color:#666;font-size:11px;margin:0;">SkyFlow Airlines | This is an automated email. Do not reply.</p>
            </div>
          </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        print(f"[EMAIL] Sent booking confirmation to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Error sending to {to_email}: {e}")
        return False

# ===== DATABASE =====
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initialize database"""
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            password    TEXT    NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'user' CHECK(role IN ('user','admin')),
            phone       TEXT,
            address     TEXT,
            city        TEXT,
            state       TEXT,
            postal_code TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Flights table
    c.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            id          TEXT    PRIMARY KEY,
            airline     TEXT    NOT NULL,
            origin      TEXT    NOT NULL,
            destination TEXT    NOT NULL,
            departure   TEXT    NOT NULL,
            arrival     TEXT    NOT NULL,
            duration    TEXT    NOT NULL,
            total_seats INTEGER NOT NULL DEFAULT 180,
            available_seats INTEGER NOT NULL DEFAULT 180,
            fare        REAL    NOT NULL,
            status      TEXT    NOT NULL DEFAULT 'active'
        )
    """)

    # Bookings table
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id            TEXT    PRIMARY KEY,
            user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            flight_id     TEXT    NOT NULL REFERENCES flights(id),
            booking_type  TEXT    NOT NULL DEFAULT 'regular',
            seat_pref     TEXT    DEFAULT 'Window',
            meal_pref     TEXT    DEFAULT 'Vegetarian',
            payment_method TEXT   DEFAULT 'Card',
            fare          REAL    NOT NULL,
            travel_date   TEXT    NOT NULL,
            status        TEXT    NOT NULL DEFAULT 'confirmed',
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Rewards table
    c.execute("""
        CREATE TABLE IF NOT EXISTS rewards (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            total_points INTEGER NOT NULL DEFAULT 0,
            tier        TEXT    NOT NULL DEFAULT 'Bronze'
        )
    """)

    # Seed default data
    c.execute("SELECT COUNT(*) as cnt FROM users")
    if c.fetchone()['cnt'] == 0:
        # Add default users
        c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                  ("AQIB MAJEED", "user@skyflow.com", hash_password("password123"), "user"))
        c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                  ("Admin", "admin@skyflow.com", hash_password("admin123"), "admin"))

        # Add rewards for users
        c.execute("INSERT INTO rewards (user_id, total_points, tier) VALUES (1, 250, 'Bronze')")
        c.execute("INSERT INTO rewards (user_id, total_points, tier) VALUES (2, 1000, 'Silver')")

    # Seed flights
    c.execute("SELECT COUNT(*) as cnt FROM flights")
    if c.fetchone()['cnt'] == 0:
        flights = [
            ("AI-101", "Air India",  "DEL", "BOM", "08:00", "10:30", "2h 30m", 180, 45,  2500.0),
            ("SG-205", "SpiceJet",   "DEL", "BOM", "14:15", "17:00", "2h 45m", 180, 32,  1950.0),
            ("6E-302", "IndiGo",     "BLR", "DEL", "19:30", "22:15", "2h 45m", 180, 2,   3100.0),
            ("UK-511", "Vistara",    "HYD", "BOM", "11:00", "12:45", "1h 45m", 180, 115, 2200.0),
            ("AI-202", "Air India",  "BOM", "HYD", "09:30", "11:15", "1h 45m", 180, 60,  2800.0),
            ("SG-310", "SpiceJet",   "MAA", "BLR", "07:00", "08:15", "1h 15m", 180, 78,  1200.0),
            ("6E-401", "IndiGo",     "DEL", "HYD", "16:00", "18:30", "2h 30m", 180, 20,  2650.0),
        ]
        for f in flights:
            c.execute("""INSERT INTO flights 
                (id, airline, origin, destination, departure, arrival, duration, total_seats, available_seats, fare)
                VALUES (?,?,?,?,?,?,?,?,?,?)""", f)

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

# ===== AUTH HELPERS =====
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth = request.headers['Authorization']
            try:
                token = auth.split(" ")[1]
            except (IndexError, ValueError):
                return {"success": False, "error": "Invalid token format"}, 401

        if not token:
            return {"success": False, "error": "Token missing"}, 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = data.get('user_id')
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": "Token expired"}, 401
        except Exception:
            return {"success": False, "error": "Invalid token"}, 401

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        conn.close()

        if not user:
            return {"success": False, "error": "User not found"}, 401

        g.current_user = dict(user)
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.current_user['role'] != 'admin':
            return {"success": False, "error": "Admin access required"}, 403
        return f(*args, **kwargs)
    return decorated

def create_jwt_token(user_id):
    token = jwt.encode({'user_id': user_id, 'exp': datetime.now(timezone.utc) + timedelta(days=30)}, SECRET_KEY, algorithm="HS256")
    # Handles older versions of PyJWT gracefully where encode returns bytes
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

# ===== STATIC FILES =====
@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index_resp.html")

@app.route("/<path:filename>")
def serve_file(filename):
    return send_from_directory(STATIC_DIR, filename)

# ===== AUTH ROUTES =====
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not name or not email or not password:
        return {"success": False, "error": "Missing required fields"}, 400

    if len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters"}, 400

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE email = ?", (email,))
    if c.fetchone():
        conn.close()
        return {"success": False, "error": "Email already registered"}, 400

    try:
        c.execute("""INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)""",
                  (name, email, hash_password(password), "user"))
        user_id = c.lastrowid
        c.execute("INSERT INTO rewards (user_id, total_points, tier) VALUES (?, 0, ?)", (user_id, "Bronze"))
        conn.commit()

        user = c.execute("SELECT id, name, email, role FROM users WHERE id = ?", (user_id,)).fetchone()
        token = create_jwt_token(user['id'])

        conn.close()
        return {
            "success": True,
            "data": {
                "token": token,
                "user": dict(user)
            }
        }, 201
    except Exception as e:
        conn.close()
        return {"success": False, "error": str(e)}, 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if not email or not password:
        return {"success": False, "error": "Email and password required"}, 400

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()

    if not user or user['password'] != hash_password(password):
        return {"success": False, "error": "Invalid email or password"}, 401

    token = create_jwt_token(user['id'])

    return {
        "success": True,
        "data": {
            "token": token,
            "user": {
                "id": user['id'],
                "name": user['name'],
                "email": user['email'],
                "role": user['role']
            }
        }
    }, 200

@app.route("/api/auth/logout", methods=["POST"])
@token_required
def logout():
    return {"success": True, "data": {"message": "Logged out"}}, 200

@app.route("/api/auth/me", methods=["GET"])
@token_required
def get_me():
    return {
        "success": True,
        "data": {
            "id": g.current_user['id'],
            "name": g.current_user['name'],
            "email": g.current_user['email'],
            "role": g.current_user['role']
        }
    }, 200

# ===== FLIGHT ROUTES =====
@app.route("/api/flights", methods=["GET"])
def search_flights():
    from_city = request.args.get('from', '').upper()
    to_city = request.args.get('to', '').upper()

    if not from_city or not to_city:
        return {"success": False, "error": "From and To required"}, 400

    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT id, airline, origin, destination, departure, arrival, duration, 
                 available_seats, fare FROM flights WHERE origin = ? AND destination = ?""",
              (from_city, to_city))
    flights = c.fetchall()
    conn.close()

    result = []
    for f in flights:
        fd = dict(f)
        fd['from_city'] = fd['origin']
        fd['to_city'] = fd['destination']
        fd['dep_time'] = fd['departure']
        fd['arr_time'] = fd['arrival']
        fd['avail_seats'] = fd['available_seats']
        result.append(fd)

    return {
        "success": True,
        "data": result
    }, 200

@app.route("/api/flights/all", methods=["GET"])
@admin_required
def get_all_flights():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM flights")
    flights = c.fetchall()
    conn.close()

    result = []
    for f in flights:
        fd = dict(f)
        fd['from_city'] = fd['origin']
        fd['to_city'] = fd['destination']
        fd['dep_time'] = fd['departure']
        fd['arr_time'] = fd['arrival']
        fd['avail_seats'] = fd['available_seats']
        result.append(fd)

    return {
        "success": True,
        "data": result
    }, 200

# ===== BOOKING ROUTES =====
@app.route("/api/bookings", methods=["GET"])
@token_required
def get_my_bookings():
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT b.*, f.airline, f.origin as from_city, f.destination as to_city, f.departure, f.arrival
                 FROM bookings b JOIN flights f ON b.flight_id = f.id WHERE b.user_id = ? ORDER BY b.created_at DESC""",
              (g.current_user['id'],))
    bookings = c.fetchall()
    conn.close()

    return {
        "success": True,
        "data": [dict(b) for b in bookings]
    }, 200

@app.route("/api/bookings", methods=["POST"])
@token_required
def create_booking():
    data = request.get_json(silent=True) or {}
    flight_id = data.get('flight_id')
    travel_date = data.get('travel_date')
    seat_pref = data.get('seat_pref', 'Window')
    meal_pref = data.get('meal_pref', 'Vegetarian')
    payment_method = data.get('payment_method') or data.get('payment', 'Card')
    passenger_name = data.get('passenger_name', g.current_user.get('name', 'Passenger'))
    passenger_age = data.get('passenger_age', '')
    passenger_email = data.get('passenger_email', '')
    passenger_phone = data.get('passenger_phone', '')

    if not flight_id or not travel_date:
        return {"success": False, "error": "Flight and date required"}, 400

    conn = get_db()
    c = conn.cursor()

    # Get flight
    c.execute("SELECT * FROM flights WHERE id = ?", (flight_id,))
    flight = c.fetchone()
    if not flight:
        conn.close()
        return {"success": False, "error": "Flight not found"}, 404

    # Create booking
    booking_id = f"#BK{int(datetime.now().timestamp())}"
    c.execute("""INSERT INTO bookings 
                 (id, user_id, flight_id, seat_pref, meal_pref, payment_method, fare, travel_date, booking_type)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (booking_id, g.current_user['id'], flight_id, seat_pref, meal_pref, payment_method, flight['fare'], travel_date, "regular"))

    # Update available seats
    c.execute("UPDATE flights SET available_seats = available_seats - 1 WHERE id = ?", (flight_id,))

    # Add reward points (250 per booking)
    c.execute("UPDATE rewards SET total_points = total_points + 250 WHERE user_id = ?", (g.current_user['id'],))

    conn.commit()
    conn.close()

    # Send email confirmation
    if passenger_email:
        send_booking_email(
            to_email=passenger_email,
            passenger_name=passenger_name,
            booking_id=booking_id,
            flight_id=flight_id,
            from_city=flight['origin'],
            to_city=flight['destination'],
            dep_time=flight['departure'],
            arr_time=flight['arrival'],
            travel_date=travel_date,
            fare=flight['fare'],
            seat=seat_pref,
            meal=meal_pref,
            payment=payment_method
        )

    return {
        "success": True,
        "data": {
            "booking_id": booking_id,
            "flight_id": flight_id,
            "fare": flight['fare'],
            "travel_date": travel_date
        }
    }, 201

@app.route("/api/bookings/emergency", methods=["POST"])
@token_required
def create_emergency_booking():
    data = request.get_json(silent=True) or {}
    flight_id = data.get('flight_id')
    travel_date = data.get('travel_date')
    seat_pref = data.get('seat_pref', 'Window')
    meal_pref = data.get('meal_pref', 'Vegetarian')
    payment_method = data.get('payment_method') or data.get('payment', 'Card')

    if not flight_id or not travel_date:
        return {"success": False, "error": "Flight and date required"}, 400

    conn = get_db()
    c = conn.cursor()

    # Get flight
    c.execute("SELECT * FROM flights WHERE id = ?", (flight_id,))
    flight = c.fetchone()
    if not flight:
        conn.close()
        return {"success": False, "error": "Flight not found"}, 404

    # Create booking
    booking_id = f"#BK{int(datetime.now().timestamp())}"
    c.execute("""INSERT INTO bookings 
                 (id, user_id, flight_id, seat_pref, meal_pref, payment_method, fare, travel_date, booking_type)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (booking_id, g.current_user['id'], flight_id, seat_pref, meal_pref, payment_method, flight['fare'], travel_date, "emergency"))

    # Update available seats
    c.execute("UPDATE flights SET available_seats = available_seats - 1 WHERE id = ?", (flight_id,))

    # Add reward points
    c.execute("UPDATE rewards SET total_points = total_points + 250 WHERE user_id = ?", (g.current_user['id'],))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "data": {
            "booking_id": booking_id,
            "flight_id": flight_id,
            "fare": flight['fare'],
            "travel_date": travel_date,
            "from_city": flight['origin'],
            "to_city": flight['destination'],
            "dep_time": flight['departure'],
            "arr_time": flight['arrival']
        }
    }, 201

@app.route("/api/bookings/elder", methods=["POST"])
@token_required
def create_elder_booking():
    data = request.get_json(silent=True) or {}
    flight_id = data.get('flight_id')
    travel_date = data.get('travel_date')
    seat_pref = data.get('seat_pref', 'Aisle')
    meal_pref = data.get('meal_pref', 'Vegetarian')
    payment_method = data.get('payment_method') or data.get('payment', 'Card')

    if not flight_id or not travel_date:
        return {"success": False, "error": "Flight and date required"}, 400

    conn = get_db()
    c = conn.cursor()

    # Get flight
    c.execute("SELECT * FROM flights WHERE id = ?", (flight_id,))
    flight = c.fetchone()
    if not flight:
        conn.close()
        return {"success": False, "error": "Flight not found"}, 404

    # Create booking
    booking_id = f"#BK{int(datetime.now().timestamp())}"
    c.execute("""INSERT INTO bookings 
                 (id, user_id, flight_id, seat_pref, meal_pref, payment_method, fare, travel_date, booking_type)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (booking_id, g.current_user['id'], flight_id, seat_pref, meal_pref, payment_method, flight['fare'], travel_date, "elder"))

    # Update available seats
    c.execute("UPDATE flights SET available_seats = available_seats - 1 WHERE id = ?", (flight_id,))

    # Add reward points
    c.execute("UPDATE rewards SET total_points = total_points + 250 WHERE user_id = ?", (g.current_user['id'],))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "data": {
            "booking_id": booking_id,
            "flight_id": flight_id,
            "fare": flight['fare'],
            "travel_date": travel_date,
            "from_city": flight['origin'],
            "to_city": flight['destination'],
            "dep_time": flight['departure'],
            "arr_time": flight['arrival']
        }
    }, 201

@app.route("/api/bookings/student", methods=["POST"])
@token_required
def create_student_booking():
    data = request.get_json(silent=True) or {}
    flight_id = data.get('flight_id')
    travel_date = data.get('travel_date')
    student_name = data.get('student_name', g.current_user.get('name', 'Student'))
    student_id = data.get('student_id', '')
    identity_number = data.get('identity_number', '')
    seat_pref = data.get('seat_pref', 'Window')
    meal_pref = data.get('meal_pref', 'Vegetarian')
    payment_method = data.get('payment_method') or data.get('payment', 'Card')

    if not flight_id or not travel_date:
        return {"success": False, "error": "Flight and date required"}, 400
    if not student_id:
        return {"success": False, "error": "Student ID is required"}, 400

    conn = get_db()
    c = conn.cursor()

    # Get flight
    c.execute("SELECT * FROM flights WHERE id = ?", (flight_id,))
    flight = c.fetchone()
    if not flight:
        conn.close()
        return {"success": False, "error": "Flight not found"}, 404

    # Create booking
    booking_id = f"#BK{int(datetime.now().timestamp())}"
    c.execute("""INSERT INTO bookings 
                 (id, user_id, flight_id, seat_pref, meal_pref, payment_method, fare, travel_date, booking_type)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (booking_id, g.current_user['id'], flight_id, seat_pref, meal_pref, payment_method, flight['fare'], travel_date, "student"))

    # Update available seats
    c.execute("UPDATE flights SET available_seats = available_seats - 1 WHERE id = ?", (flight_id,))

    # Add reward points
    c.execute("UPDATE rewards SET total_points = total_points + 250 WHERE user_id = ?", (g.current_user['id'],))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "data": {
            "booking_id": booking_id,
            "flight_id": flight_id,
            "fare": flight['fare'],
            "travel_date": travel_date,
            "from_city": flight['origin'],
            "to_city": flight['destination'],
            "dep_time": flight['departure'],
            "arr_time": flight['arrival']
        }
    }, 201

@app.route("/api/bookings/<booking_id>", methods=["DELETE"])
@token_required
def cancel_booking(booking_id):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM bookings WHERE id = ? AND user_id = ?", (booking_id, g.current_user['id']))
    booking = c.fetchone()

    if not booking:
        conn.close()
        return {"success": False, "error": "Booking not found"}, 404

    if booking['status'] == 'cancelled':
        conn.close()
        return {"success": False, "error": "Booking already cancelled"}, 400

    fare = booking['fare']
    c.execute("UPDATE bookings SET status = ? WHERE id = ?", ("cancelled", booking_id))
    c.execute("UPDATE flights SET available_seats = available_seats + 1 WHERE id = ?", (booking['flight_id'],))

    conn.commit()
    conn.close()

    return {"success": True, "data": {"message": "Booking cancelled successfully. Refund of \u20b9" + str(int(fare)) + " will be credited to your account within 5-7 business days.", "refund": fare}}, 200

# ===== REWARDS ROUTES =====
@app.route("/api/rewards", methods=["GET"])
@token_required
def get_rewards():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT total_points, tier FROM rewards WHERE user_id = ?", (g.current_user['id'],))
    reward = c.fetchone()
    conn.close()

    if not reward:
        return {
            "success": True,
            "data": {"total_points": 0, "tier": "Bronze", "balance": 0}
        }, 200

    return {
        "success": True,
        "data": {
            "total_points": reward['total_points'],
            "tier": reward['tier'],
            "balance": reward['total_points']
        }
    }, 200

@app.route("/api/rewards/redeem", methods=["POST"])
@token_required
def redeem_reward():
    data = request.get_json(silent=True) or {}
    reward_name = data.get('reward_name')

    if not reward_name:
        return {"success": False, "error": "Reward name required"}, 400

    # Cost mapping
    costs = {
        "Free Flight": 10000,
        "Hotel Stay": 8000,
        "Meal Voucher": 1500,
        "Extra Baggage": 2000
    }

    cost = costs.get(reward_name, 0)
    if cost == 0:
        return {"success": False, "error": "Invalid reward"}, 400

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT total_points FROM rewards WHERE user_id = ?", (g.current_user['id'],))
    reward = c.fetchone()

    if not reward or reward['total_points'] < cost:
        conn.close()
        return {"success": False, "error": "Insufficient points"}, 400

    c.execute("UPDATE rewards SET total_points = total_points - ? WHERE user_id = ?",
              (cost, g.current_user['id']))
    conn.commit()
    conn.close()

    return {"success": True, "data": {"message": f"Redeemed {reward_name}"}}, 200

# ===== PROFILE ROUTES =====
@app.route("/api/profile", methods=["GET"])
@token_required
def get_profile():
    return {
        "success": True,
        "data": {
            "id": g.current_user['id'],
            "name": g.current_user['name'],
            "email": g.current_user['email']
        }
    }, 200

@app.route("/api/profile", methods=["PATCH", "PUT"])
@token_required
def update_profile():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    phone = data.get('phone')

    conn = get_db()
    c = conn.cursor()

    if name:
        c.execute("UPDATE users SET name = ? WHERE id = ?", (name, g.current_user['id']))
    if phone:
        c.execute("UPDATE users SET phone = ? WHERE id = ?", (phone, g.current_user['id']))

    conn.commit()

    c.execute("SELECT id, name, email, role FROM users WHERE id = ?", (g.current_user['id'],))
    user = c.fetchone()
    conn.close()

    return {
        "success": True,
        "data": dict(user)
    }, 200

# ===== ADMIN ROUTES =====
@app.route("/api/admin/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as total FROM users WHERE role = 'user'")
    users = c.fetchone()['total']

    c.execute("SELECT COUNT(*) as total FROM bookings")
    bookings = c.fetchone()['total']

    c.execute("SELECT COUNT(*) as total FROM bookings WHERE booking_type = 'emergency'")
    emergency_bookings = c.fetchone()['total']

    c.execute("SELECT SUM(fare) as total FROM bookings")
    revenue = c.fetchone()['total'] or 0

    c.execute("""SELECT b.id, b.fare, b.travel_date, b.booking_type as type, u.email as user_email, f.origin as from_city, f.destination as to_city 
                 FROM bookings b 
                 JOIN flights f ON b.flight_id = f.id 
                 JOIN users u ON b.user_id = u.id 
                 ORDER BY b.created_at DESC LIMIT 5""")
    recent = [dict(b) for b in c.fetchall()]

    conn.close()

    return {
        "success": True,
        "data": {
            "total_users": users,
            "total_bookings": bookings,
            "emergency_bookings": emergency_bookings,
            "total_revenue": revenue,
            "recent": recent
        }
    }, 200

@app.route("/api/admin/bookings", methods=["GET"])
@admin_required
def admin_bookings():
    book_type = request.args.get('type', 'all')

    conn = get_db()
    c = conn.cursor()

    if book_type == 'all':
        c.execute("""SELECT b.*, f.airline, f.origin as from_city, f.destination as to_city,
                     u.name, u.email as user_email FROM bookings b 
                     JOIN flights f ON b.flight_id = f.id 
                     JOIN users u ON b.user_id = u.id ORDER BY b.created_at DESC""")
    else:
        c.execute("""SELECT b.*, f.airline, f.origin as from_city, f.destination as to_city,
                     u.name, u.email as user_email FROM bookings b 
                     JOIN flights f ON b.flight_id = f.id 
                     JOIN users u ON b.user_id = u.id 
                     WHERE b.booking_type = ? ORDER BY b.created_at DESC""", (book_type,))

    bookings = c.fetchall()
    conn.close()

    result = []
    for b in bookings:
        bd = dict(b)
        bd['type'] = bd.get('booking_type', 'regular')
        result.append(bd)

    return {
        "success": True,
        "data": result
    }, 200

@app.route("/api/admin/users", methods=["GET"])
@admin_required
def admin_users():
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT u.id, u.name, u.email, u.role, u.created_at, 
                 (SELECT tier FROM rewards r WHERE r.user_id = u.id) as tier,
                 (SELECT total_points FROM rewards r WHERE r.user_id = u.id) as total_points,
                 (SELECT COUNT(id) FROM bookings b WHERE b.user_id = u.id) as booking_count 
                 FROM users u ORDER BY u.created_at DESC""")
    users = c.fetchall()
    conn.close()

    result = []
    for u in users:
        ud = dict(u)
        ud['points'] = ud.get('total_points', 0)
        result.append(ud)

    return {
        "success": True,
        "data": result
    }, 200

@app.route("/api/admin/analytics", methods=["GET"])
@admin_required
def admin_analytics():
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) as total FROM users WHERE role = 'user'")
    total_users = c.fetchone()['total']

    c.execute("SELECT COUNT(*) as total FROM bookings")
    total_bookings = c.fetchone()['total']

    c.execute("SELECT COUNT(*) as total FROM bookings WHERE booking_type = 'emergency'")
    emergency_bookings = c.fetchone()['total']

    c.execute("SELECT COUNT(*) as total FROM bookings WHERE booking_type = 'elder'")
    elder_bookings = c.fetchone()['total']

    c.execute("SELECT COUNT(*) as total FROM bookings WHERE booking_type = 'regular'")
    regular_bookings = c.fetchone()['total']

    c.execute("SELECT SUM(fare) as total FROM bookings")
    total_revenue = c.fetchone()['total'] or 0

    # Payment distribution
    c.execute("SELECT payment_method, COUNT(*) as cnt FROM bookings GROUP BY payment_method")
    pay_dist_rows = c.fetchall()
    payment_distribution = {}
    for row in pay_dist_rows:
        payment_distribution[row['payment_method']] = row['cnt']

    # Daily revenue for chart
    c.execute("""SELECT date(created_at) as day, SUM(fare) as rev 
                 FROM bookings WHERE status != 'cancelled'
                 GROUP BY date(created_at) 
                 ORDER BY day ASC""")
    daily_revenue = [{"date": r['day'], "revenue": r['rev'] or 0} for r in c.fetchall()]

    # Monthly revenue for chart
    c.execute("""SELECT strftime('%Y-%m', created_at) as month, SUM(fare) as rev 
                 FROM bookings WHERE status != 'cancelled'
                 GROUP BY strftime('%Y-%m', created_at) 
                 ORDER BY month ASC""")
    monthly_revenue = [{"month": r['month'], "revenue": r['rev'] or 0} for r in c.fetchall()]

    conn.close()

    return {
        "success": True,
        "data": {
            "users": total_users,
            "bookings": total_bookings,
            "emergency": emergency_bookings,
            "elder": elder_bookings,
            "regular": regular_bookings,
            "revenue": total_revenue,
            "payment_distribution": payment_distribution,
            "daily_revenue": daily_revenue,
            "monthly_revenue": monthly_revenue
        }
    }, 200

# ===== ADMIN FLIGHT MANAGEMENT =====
@app.route("/api/admin/flights/add", methods=["POST"])
@admin_required
def admin_add_flight():
    data = request.get_json(silent=True) or {}
    flight_id = data.get('id', '').strip()
    airline = data.get('airline', '').strip()
    origin = data.get('origin', '').strip().upper()
    destination = data.get('destination', '').strip().upper()
    departure = data.get('departure', '').strip()
    arrival = data.get('arrival', '').strip()
    duration = data.get('duration', '').strip()
    total_seats = int(data.get('total_seats', 180))
    fare = float(data.get('fare', 0))

    if not all([flight_id, airline, origin, destination, departure, arrival, duration, fare]):
        return {"success": False, "error": "All fields are required"}, 400

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT id FROM flights WHERE id = ?", (flight_id,))
    if c.fetchone():
        conn.close()
        return {"success": False, "error": "Flight ID already exists"}, 400

    c.execute("""INSERT INTO flights (id, airline, origin, destination, departure, arrival, duration, total_seats, available_seats, fare)
                 VALUES (?,?,?,?,?,?,?,?,?,?)""",
              (flight_id, airline, origin, destination, departure, arrival, duration, total_seats, total_seats, fare))
    conn.commit()
    conn.close()

    return {"success": True, "data": {"message": "Flight " + flight_id + " added successfully"}}, 201

@app.route("/api/admin/flights/<flight_id>", methods=["PUT", "PATCH"])
@admin_required
def admin_edit_flight(flight_id):
    data = request.get_json(silent=True) or {}

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM flights WHERE id = ?", (flight_id,))
    flight = c.fetchone()
    if not flight:
        conn.close()
        return {"success": False, "error": "Flight not found"}, 404

    if 'fare' in data:
        c.execute("UPDATE flights SET fare = ? WHERE id = ?", (float(data['fare']), flight_id))
    if 'available_seats' in data:
        c.execute("UPDATE flights SET available_seats = ? WHERE id = ?", (int(data['available_seats']), flight_id))
    if 'total_seats' in data:
        c.execute("UPDATE flights SET total_seats = ? WHERE id = ?", (int(data['total_seats']), flight_id))
    if 'status' in data:
        c.execute("UPDATE flights SET status = ? WHERE id = ?", (data['status'], flight_id))
    if 'departure' in data:
        c.execute("UPDATE flights SET departure = ? WHERE id = ?", (data['departure'], flight_id))
    if 'arrival' in data:
        c.execute("UPDATE flights SET arrival = ? WHERE id = ?", (data['arrival'], flight_id))

    conn.commit()

    c.execute("SELECT * FROM flights WHERE id = ?", (flight_id,))
    updated = dict(c.fetchone())
    conn.close()

    return {"success": True, "data": updated}, 200

@app.route("/api/admin/flights/<flight_id>", methods=["DELETE"])
@admin_required
def admin_delete_flight(flight_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM flights WHERE id = ?", (flight_id,))
    if not c.fetchone():
        conn.close()
        return {"success": False, "error": "Flight not found"}, 404
    c.execute("UPDATE flights SET status = 'inactive' WHERE id = ?", (flight_id,))
    conn.commit()
    conn.close()
    return {"success": True, "data": {"message": "Flight deactivated"}}, 200

@app.route("/api/admin/bookings/<booking_id>/cancel", methods=["POST"])
@admin_required
def admin_cancel_booking(booking_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    booking = c.fetchone()
    if not booking:
        conn.close()
        return {"success": False, "error": "Booking not found"}, 404
    if booking['status'] == 'cancelled':
        conn.close()
        return {"success": False, "error": "Booking already cancelled"}, 400

    fare = booking['fare']
    c.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))
    c.execute("UPDATE flights SET available_seats = available_seats + 1 WHERE id = ?", (booking['flight_id'],))
    conn.commit()
    conn.close()

    return {"success": True, "data": {"message": "Booking cancelled. Refund of \u20b9" + str(int(fare)) + " will be credited to the customer's account within 5-7 business days.", "refund": fare}}, 200

# ===== ERROR HANDLERS =====
@app.errorhandler(404)
def not_found(error):
    return {"success": False, "error": "Not found"}, 404

@app.errorhandler(500)
def server_error(error):
    return {"success": False, "error": "Server error"}, 500

# ===== MAIN =====
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5001)
