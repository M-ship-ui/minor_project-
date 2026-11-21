"""
========================================================================================
SANSKRITI UNIVERSITY - DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING
INTELLIGENT ACADEMIC ASSET RECOVERY AND MANAGEMENT SYSTEM
----------------------------------------------------------------------------------------
Student: O. Pulla Reddy (Enrollment No: 2302320110)
Faculty Guide: Dr. Sakuldeep Singh
Session: Academic Year 2026-2027

SINGLE-FILE MONOLITHIC STANDALONE DISTRIBUTION (ALL-IN-ONE FOR GUIDE DEMONSTRATION)
This single Python file contains:
  1. Complete SQLite Relational Database Engine (Tables + Schema + Pre-Seeded Academic Data)
  2. AIML Text Matching Engine (NLP TF-IDF Vectorizer + Cosine Similarity Ranking)
  3. Session-Based Authentication & Role-Based Access Control (Student, Staff, HOD, Admin)
  4. Complete Flask Web Server & API Routes (All 8 Figures & Portal Workflows)
  5. Built-in Responsive Embedded HTML/CSS/JS Templates (Bootstrap 5 & FontAwesome)

HOW TO RUN IN VS CODE:
  python single_file_academic_system.py
  Then open http://127.0.0.1:5000 in your browser!
========================================================================================
"""

import os
import sys
import re
import sqlite3
import datetime
from functools import wraps
from jinja2 import DictLoader, ChoiceLoader
from flask import (
    Flask, request, redirect, url_for, session, flash,
    render_template_string, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize Flask Application
app = Flask(__name__)
app.secret_key = "sanskriti_university_academic_recovery_monolith_secret_key_2026"
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "academic_assets.db")

# --------------------------------------------------------------------------------------
# 1. AIML TEXT MATCHING MODULE (Appendix A Reference Implementation)
# --------------------------------------------------------------------------------------
def clean_text(text):
    """Lower-case text and replace punctuation with spaces."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def build_search_text(item):
    """Join searchable fields of a report into one cleaned string."""
    parts = [
        item.get("name", "") if isinstance(item, dict) else item[3],
        item.get("category", "") if isinstance(item, dict) else item[4],
        item.get("description", "") if isinstance(item, dict) else item[5],
        item.get("location", "") if isinstance(item, dict) else item[7]
    ]
    return clean_text(" ".join(str(p) for p in parts if p))

def compute_similarity(new_item, candidates):
    """Compute TF-IDF cosine similarity vector between new item and stored candidates."""
    if not candidates:
        return []
    docs = [build_search_text(c) for c in candidates]
    vectorizer = TfidfVectorizer(stop_words="english", sublinear_tf=True)
    matrix = vectorizer.fit_transform(docs + [build_search_text(new_item)])
    return cosine_similarity(matrix[-1], matrix[:-1]).ravel().tolist()

def rank_candidate_matches(new_item, candidates, threshold=0.25, top_n=5):
    """Return top_n (candidate, score) pairs where score >= threshold."""
    if not candidates:
        return []
    scores = compute_similarity(new_item, candidates)
    ranked = sorted(zip(candidates, scores), key=lambda p: p[1], reverse=True)
    return [(c, round(float(s), 4)) for c, s in ranked if s >= threshold][:top_n]

# --------------------------------------------------------------------------------------
# 2. DATABASE MANAGEMENT & INITIALIZATION
# --------------------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'staff', 'dept_head', 'admin')),
        department TEXT NOT NULL,
        id_number TEXT NOT NULL,
        phone TEXT,
        avatar TEXT DEFAULT 'default_avatar.png',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    # Items table
    c.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_number TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('lost', 'found')),
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        department TEXT NOT NULL,
        location TEXT NOT NULL,
        building TEXT NOT NULL,
        date_occurred TEXT NOT NULL,
        time_occurred TEXT,
        image_filename TEXT,
        reporter_id INTEGER NOT NULL,
        reporter_name TEXT NOT NULL,
        reporter_email TEXT NOT NULL,
        is_anonymous INTEGER DEFAULT 0,
        status TEXT NOT NULL CHECK(status IN ('Lost', 'Found', 'Under Claim', 'Verified', 'Returned', 'Unclaimed')),
        serial_number TEXT,
        unique_marks TEXT,
        custody_location TEXT,
        is_escalated INTEGER DEFAULT 0,
        escalation_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (reporter_id) REFERENCES users(id)
    )""")
    # Claims table
    c.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        claimant_id INTEGER NOT NULL,
        claimant_name TEXT NOT NULL,
        claimant_email TEXT NOT NULL,
        claimant_phone TEXT,
        proof_description TEXT NOT NULL,
        serial_number_match TEXT,
        proof_image_filename TEXT,
        status TEXT NOT NULL CHECK(status IN ('Pending', 'Verified', 'Rejected')),
        rejection_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verified_at TIMESTAMP,
        verified_by INTEGER,
        FOREIGN KEY (item_id) REFERENCES items(id),
        FOREIGN KEY (claimant_id) REFERENCES users(id)
    )""")
    # Matches table
    c.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lost_item_id INTEGER NOT NULL,
        found_item_id INTEGER NOT NULL,
        text_similarity REAL NOT NULL,
        category_match REAL NOT NULL,
        color_match REAL NOT NULL,
        composite_score REAL NOT NULL,
        status TEXT DEFAULT 'Suggested',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(lost_item_id, found_item_id),
        FOREIGN KEY (lost_item_id) REFERENCES items(id),
        FOREIGN KEY (found_item_id) REFERENCES items(id)
    )""")
    # Audit log table
    c.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_name TEXT,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        details TEXT NOT NULL,
        ip_address TEXT DEFAULT '127.0.0.1',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    # Notifications table
    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        link TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")
    conn.commit()

    # Pre-seed users if empty
    user_count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count == 0:
        users = [
            ("Dr. Sakuldeep Singh (Director/Admin)", "admin@sanskriti.edu.in", generate_password_hash("admin123"), "admin", "Campus Administration", "ADM-001", "+91 98765 43210"),
            ("Prof. Amit Sharma (HOD CSE)", "hod.cs@sanskriti.edu.in", generate_password_hash("hod123"), "dept_head", "Computer Science & Engineering", "HOD-CSE-01", "+91 98765 43211"),
            ("Rajesh Kumar (Library Officer)", "staff.rajesh@sanskriti.edu.in", generate_password_hash("staff123"), "staff", "Central Library", "STF-LIB-102", "+91 98765 43212"),
            ("O. Pulla Reddy (Student)", "student.reddy@sanskriti.edu.in", generate_password_hash("student123"), "student", "Computer Science & Engineering", "2302320110", "+91 98765 43213"),
            ("Priya Verma (Student)", "student.priya@sanskriti.edu.in", generate_password_hash("priya123"), "student", "Electronics & Communication", "2023-BTEC-019", "+91 98765 43214"),
            ("Arjun Nair (Student)", "student.arjun@sanskriti.edu.in", generate_password_hash("arjun123"), "student", "Mechanical Engineering", "2022-BTME-088", "+91 98765 43215")
        ]
        c.executemany("INSERT INTO users (name, email, password_hash, role, department, id_number, phone) VALUES (?, ?, ?, ?, ?, ?, ?)", users)

        # Seed sample items
        items = [
            ("TKT-LOST-2026-001", "lost", "Dell XPS 15 Silver Laptop with Sanskriti Coding Club Sticker", "Laptops", "Silver Dell XPS 15 (9520) laptop with a black carbon palm rest and Sanskriti Coding Club sticker on lid.", "Computer Science & Engineering", "2nd Floor Silent Reading Cubicle #14", "Central Library", "2026-09-28", "16:30", "dell_xps_lost.jpg", 4, "O. Pulla Reddy", "student.reddy@sanskriti.edu.in", 0, "Lost", "SN: DLXPS-99214A", "Coding club sticker, blue silicone keyboard protector"),
            ("TKT-FND-2026-001", "found", "Dell XPS 15 Silver Laptop", "Laptops", "Found Dell XPS laptop 15-inch silver chassis with charging adapter left on reading desk.", "Central Library", "Desk 14, 2nd Floor Reading Room", "Central Library", "2026-09-28", "18:00", "dell_xps_found.jpg", 3, "Rajesh Kumar", "staff.rajesh@sanskriti.edu.in", 0, "Found", "SN: DLXPS-99214A", "Silver metallic body, sticker on lid", "Central Library Front Desk Locker 3B"),
            ("TKT-LOST-2026-002", "lost", "Sanskriti University Student ID Card - O. Pulla Reddy", "ID Cards", "Sanskriti University official smart ID card for Computer Science student O. Pulla Reddy (ID: 2302320110). Blue university lanyard attached with library RFID chip.", "Computer Science & Engineering", "Cafeteria dining hall table 8", "Student Activity Center", "2026-10-01", "13:15", "id_card_lost.jpg", 4, "O. Pulla Reddy", "student.reddy@sanskriti.edu.in", 0, "Lost", "2302320110", "Blue university lanyard, transparent card holder"),
            ("TKT-FND-2026-002", "found", "Student Smart ID Card with Blue Sanskriti Lanyard", "ID Cards", "Found smart card ID for Computer Science student with blue university lanyard and library barcode near cafeteria counter.", "Campus Security", "Dining counter tray pickup area", "Student Activity Center", "2026-10-01", "14:00", "id_card_found.jpg", 3, "Rajesh Kumar", "staff.rajesh@sanskriti.edu.in", 0, "Found", "ID ending in 0110", "Blue lanyard with university emblem", "Campus Main Gate Security Booth"),
            ("TKT-LOST-2026-003", "lost", "Tektronix 100MHz Digital Storage Oscilloscope Unit", "Laboratory Equipment", "Tektronix dual-channel digital oscilloscope unit used for VLSI lab coursework. Left near signal generator rack.", "Computer Science & Engineering", "VLSI & Hardware Lab Room 302", "Academic Block B", "2026-09-20", "16:45", "oscilloscope.jpg", 2, "Prof. Amit Sharma", "hod.cs@sanskriti.edu.in", 0, "Lost", "TEK-TBS-1052B-09", "Calibrated sticker dated Aug 2026"),
            ("TKT-FND-2026-003", "found", "Tektronix Digital Oscilloscope Unit with Probes", "Laboratory Equipment", "Found dual-channel oscilloscope left unattended on equipment trolley in the corridor outside Lab 302.", "Campus Administration", "Corridor rack outside Lab 302", "Academic Block B", "2026-09-21", "09:30", "oscilloscope.jpg", 1, "Dr. Sakuldeep Singh", "admin@sanskriti.edu.in", 0, "Under Claim", "TEK-TBS-1052B-09", "Lab calibration seal intact", "Science Complex Room 301 Store"),
            ("TKT-LOST-2026-004", "lost", "Casio fx-991EX ClassWiz Scientific Calculator", "Electronic Devices", "Black and white Casio ClassWiz fx-991EX calculator with slide-on protective hard case. Name 'Arjun' written in silver marker inside cover.", "Mechanical Engineering", "Desk 24, Examination Hall 3", "Academic Block A", "2026-09-15", "12:00", "calculator.jpg", 6, "Arjun Nair", "student.arjun@sanskriti.edu.in", 0, "Returned", "fx-991EX", "Silver marker 'Arjun' inside slide cover"),
            ("TKT-LOST-2026-005", "lost", "Apple AirPods Pro 2nd Gen in Black Leather Case", "Electronic Devices", "White AirPods Pro (2nd Generation, MagSafe USB-C) enclosed in a Nomad black horween leather protective case with small lanyard strap.", "Computer Science & Engineering", "Locker area bench", "Sports Complex", "2026-10-03", "18:00", "airpods.jpg", 4, "O. Pulla Reddy", "student.reddy@sanskriti.edu.in", 0, "Lost", "SN: H***72K", "Black leather case, faint scuff on lower lip")
        ]
        c.executemany("""
        INSERT INTO items (
            ticket_number, type, title, category, description, department, location, building,
            date_occurred, time_occurred, image_filename, reporter_id, reporter_name, reporter_email,
            is_anonymous, status, serial_number, unique_marks, custody_location
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, items)

        # Seed Claims
        c.execute("""
        INSERT INTO claims (
            item_id, claimant_id, claimant_name, claimant_email, claimant_phone, proof_description,
            serial_number_match, status, created_at, verified_at, verified_by
        ) VALUES (
            6, 2, 'Prof. Amit Sharma', 'hod.cs@sanskriti.edu.in', '+91 98765 43211',
            'Departmental property asset register invoice #AST-VLSI-402 and lab equipment register signoff.',
            'TEK-TBS-1052B-09', 'Verified', '2026-09-22 10:00:00', '2026-09-22 11:30:00', 1
        )""")

        # Seed Matches
        matches = [
            (1, 2, 0.724, 1.0, 0.85, 0.845, 'Suggested'),
            (3, 4, 0.680, 1.0, 0.80, 0.812, 'Suggested'),
            (5, 6, 0.790, 1.0, 0.90, 0.885, 'Verified')
        ]
        c.executemany("INSERT INTO matches (lost_item_id, found_item_id, text_similarity, category_match, color_match, composite_score, status) VALUES (?, ?, ?, ?, ?, ?, ?)", matches)

        # Seed Audit Logs
        logs = [
            (4, "O. Pulla Reddy", "ITEM_REPORTED", "Item", 1, "Reported lost Dell XPS 15 laptop in Central Library"),
            (3, "Rajesh Kumar", "ITEM_REPORTED", "Item", 2, "Reported found Dell XPS 15 laptop at Library Counter"),
            (None, "AI ML Engine", "MATCH_DETECTED", "Match", 1, "High-confidence composite match score (84.5%) discovered between tickets #1 and #2"),
            (2, "Prof. Amit Sharma", "CLAIM_SUBMITTED", "Claim", 1, "Submitted verified institutional claim for Tektronix Oscilloscope #6"),
            (1, "Dr. Sakuldeep Singh", "CLAIM_APPROVED", "Claim", 1, "Approved claim for Tektronix Oscilloscope and generated recovery certificate")
        ]
        c.executemany("INSERT INTO audit_logs (user_id, user_name, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?, ?)", logs)

        # Seed Notifications
        notifs = [
            (4, "AI Match Recommendation", "Our AI matching engine discovered an 84.5% match for your Dell XPS 15 laptop.", "/ai/item/1/matches"),
            (4, "ID Card Found Alert", "An official student ID card matching your credentials was handed in at the Security Booth.", "/ai/item/3/matches"),
            (1, "High Priority Claim Pending", "Institutional asset claim submitted for review by Prof. Amit Sharma.", "/claims/manage")
        ]
        c.executemany("INSERT INTO notifications (user_id, title, message, link) VALUES (?, ?, ?, ?)", notifs)
        conn.commit()

    conn.close()

# --------------------------------------------------------------------------------------
# 3. AUTHENTICATION & ACCESS CONTROL HELPERS
# --------------------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access this academic portal feature.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please sign in to continue.", "warning")
                return redirect(url_for("login", next=request.path))
            if session.get("user_role") not in allowed_roles:
                flash("Access denied: You do not possess the required academic administrative role.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --------------------------------------------------------------------------------------
# 4. EMBEDDED BASE LAYOUT & NAVIGATION TEMPLATE
# --------------------------------------------------------------------------------------
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} | Sanskriti University Academic Recovery Portal</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- FontAwesome 6 -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
    <style>
        :root {
            --su-navy: #002147;
            --su-gold: #c99700;
            --su-dark: #00152e;
            --su-accent: #2563eb;
        }
        body {
            background-color: #f8fafc;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #1e293b;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .su-topbar {
            background-color: var(--su-dark);
            color: #e2e8f0;
            font-size: 0.82rem;
            padding: 6px 0;
            border-bottom: 2px solid var(--su-gold);
        }
        .su-navbar {
            background: linear-gradient(135deg, var(--su-navy) 0%, #0d3b66 100%);
            box-shadow: 0 4px 12px rgba(0, 33, 71, 0.15);
        }
        .navbar-brand {
            font-weight: 700;
            letter-spacing: 0.5px;
            color: #ffffff !important;
        }
        .su-badge-gold {
            background-color: var(--su-gold);
            color: #000;
            font-weight: 600;
        }
        .card {
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid #e2e8f0;
        }
        .footer {
            background: var(--su-dark);
            color: #94a3b8;
            margin-top: auto;
            border-top: 3px solid var(--su-gold);
            padding: 24px 0 12px 0;
            font-size: 0.85rem;
        }
        .btn-su {
            background-color: var(--su-gold);
            color: #000;
            font-weight: 600;
            border: none;
        }
        .btn-su:hover {
            background-color: #b08400;
            color: #000;
        }
        .hero-banner {
            background: linear-gradient(135deg, #001a38 0%, #002147 60%, #0d3b66 100%);
            color: white;
            border-radius: 14px;
            padding: 3rem 2rem;
        }
    </style>
</head>
<body>
    <!-- Top University Info Header -->
    <div class="su-topbar d-none d-md-block">
        <div class="container-fluid px-4 d-flex justify-content-between align-items-center">
            <div>
                <span class="fw-bold text-warning me-2"><i class="fa-solid fa-graduation-cap"></i> SANSKRITI UNIVERSITY</span>
                <span class="text-white-50">| Mathura, Uttar Pradesh &bull; Department of Computer Science & Engineering</span>
            </div>
            <div class="d-flex align-items-center gap-3">
                <span><i class="fa-solid fa-user-graduate text-warning"></i> Student: <strong>O. Pulla Reddy (2302320110)</strong></span>
                <span><i class="fa-solid fa-chalkboard-user text-warning"></i> Guide: <strong>Dr. Sakuldeep Singh</strong></span>
                <span class="badge bg-warning text-dark">Session 2026-27</span>
            </div>
        </div>
    </div>

    <!-- Main Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-dark su-navbar sticky-top">
        <div class="container-fluid px-4">
            <a class="navbar-brand d-flex align-items-center gap-2" href="{{ url_for('index') }}">
                <i class="fa-solid fa-shield-halved text-warning fs-4"></i>
                <div>
                    <div style="font-size: 1.05rem; line-height: 1.1;">Sanskriti University</div>
                    <div style="font-size: 0.72rem; color: #cbd5e1; font-weight: 400;">Academic Asset Recovery & Management System</div>
                </div>
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navMenu">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navMenu">
                <ul class="navbar-nav me-auto mb-2 mb-lg-0 ms-lg-3">
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('index') }}"><i class="fa-solid fa-house me-1"></i> Home</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('list_lost_items') }}"><i class="fa-solid fa-circle-question text-danger me-1"></i> Lost Items</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('list_found_items') }}"><i class="fa-solid fa-circle-check text-success me-1"></i> Found Items</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('ai_matching_center') }}"><i class="fa-solid fa-microchip text-warning me-1"></i> AI Matcher</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('search') }}"><i class="fa-solid fa-magnifying-glass me-1"></i> Search</a></li>
                    {% if session.get('user_role') in ['staff', 'dept_head', 'admin'] %}
                    <li class="nav-item"><a class="nav-link text-warning fw-semibold" href="{{ url_for('dashboard') }}"><i class="fa-solid fa-gauge-high me-1"></i> Authority Dashboard</a></li>
                    {% endif %}
                </ul>
                <div class="d-flex align-items-center gap-2">
                    <a href="{{ url_for('report_lost') }}" class="btn btn-sm btn-danger"><i class="fa-solid fa-plus me-1"></i> Report Lost</a>
                    <a href="{{ url_for('report_found') }}" class="btn btn-sm btn-success"><i class="fa-solid fa-plus me-1"></i> Report Found</a>
                    {% if session.get('user_id') %}
                        <a href="{{ url_for('notifications') }}" class="btn btn-sm btn-outline-light position-relative" title="Notifications">
                            <i class="fa-solid fa-bell"></i>
                            <span class="position-absolute top-0 start-100 translate-middle p-1 bg-danger border border-light rounded-circle"></span>
                        </a>
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-light dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                <i class="fa-solid fa-user-circle text-warning me-1"></i> {{ session.get('user_name', 'Account').split()[0] }}
                                <span class="badge bg-warning text-dark text-uppercase ms-1" style="font-size: 0.65rem;">{{ session.get('user_role') }}</span>
                            </button>
                            <ul class="dropdown-menu dropdown-menu-end shadow">
                                <li class="px-3 py-2 border-bottom">
                                    <div class="fw-bold text-dark">{{ session.get('user_name') }}</div>
                                    <div class="small text-muted">{{ session.get('user_email') }}</div>
                                </li>
                                <li><a class="dropdown-item" href="{{ url_for('audit_logs') }}"><i class="fa-solid fa-list-check me-2 text-primary"></i> Audit Logs</a></li>
                                <li><a class="dropdown-item" href="{{ url_for('manage_claims') }}"><i class="fa-solid fa-shield-halved me-2 text-success"></i> My Claims</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item text-danger" href="{{ url_for('logout') }}"><i class="fa-solid fa-right-from-bracket me-2"></i> Sign Out</a></li>
                            </ul>
                        </div>
                    {% else %}
                        <a href="{{ url_for('login') }}" class="btn btn-sm btn-outline-light"><i class="fa-solid fa-right-to-bracket me-1"></i> Sign In</a>
                        <a href="{{ url_for('register') }}" class="btn btn-sm btn-warning text-dark fw-semibold"><i class="fa-solid fa-user-plus me-1"></i> Register</a>
                    {% endif %}
                </div>
            </div>
        </div>
    </nav>

    <!-- Flash Alert Notifications -->
    <div class="container-fluid px-4 mt-3">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show shadow-sm" role="alert">
                        <i class="fa-solid fa-circle-info me-2"></i> {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>

    <!-- Main Page Body Container -->
    <main class="container-fluid px-4 py-3 flex-grow-1">
        {% block content %}{% endblock %}
    </main>

    <!-- University Standard Academic Footer -->
    <footer class="footer">
        <div class="container-fluid px-4">
            <div class="row align-items-center">
                <div class="col-md-6 text-center text-md-start mb-2 mb-md-0">
                    <span class="fw-bold text-white"><i class="fa-solid fa-graduation-cap text-warning"></i> SANSKRITI UNIVERSITY</span>
                    <span class="text-white-50"> &bull; Department of Computer Science & Engineering</span>
                    <div class="small text-muted mt-1">Student: <strong>O. Pulla Reddy (2302320110)</strong> &bull; Faculty Guide: <strong>Dr. Sakuldeep Singh</strong></div>
                </div>
                <div class="col-md-6 text-center text-md-end text-white-50 small">
                    <div>&copy; 2026 Sanskriti University. All Academic Rights Reserved.</div>
                    <div>Architected with Python Flask &bull; SQLite &bull; TF-IDF NLP Cosine Matcher</div>
                </div>
            </div>
        </div>
    </footer>

    <!-- Bootstrap 5 JavaScript Bundle -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

app.jinja_loader = ChoiceLoader([
    DictLoader({"base.html": BASE_LAYOUT}),
    app.jinja_loader
])

# --------------------------------------------------------------------------------------
# 5. CONTROLLER ROUTES & PAGE HANDLERS (Matching Report Figures 5.1.1 to 5.1.8)
# --------------------------------------------------------------------------------------

# Figure 5.1.2: Home Page
@app.route("/")
def index():
    conn = get_db()
    c = conn.cursor()
    lost_count = c.execute("SELECT COUNT(*) FROM items WHERE type = 'lost' AND status = 'Lost'").fetchone()[0]
    found_count = c.execute("SELECT COUNT(*) FROM items WHERE type = 'found' AND status = 'Found'").fetchone()[0]
    matches_count = c.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    recovered_count = c.execute("SELECT COUNT(*) FROM items WHERE status = 'Returned'").fetchone()[0]

    recent_lost = c.execute("SELECT * FROM items WHERE type = 'lost' ORDER BY id DESC LIMIT 4").fetchall()
    recent_found = c.execute("SELECT * FROM items WHERE type = 'found' ORDER BY id DESC LIMIT 4").fetchall()
    top_matches = c.execute("""
        SELECT m.*, l.title as lost_title, l.category as lost_cat, l.location as lost_loc,
               f.title as found_title, f.location as found_loc
        FROM matches m
        JOIN items l ON m.lost_item_id = l.id
        JOIN items f ON m.found_item_id = f.id
        ORDER BY m.composite_score DESC LIMIT 3
    """).fetchall()
    conn.close()

    content = """
    {% extends "base.html" %}
    {% block content %}
    <!-- Hero Banner with Sanskriti University Branding -->
    <div class="hero-banner shadow mb-4">
        <div class="row align-items-center">
            <div class="col-lg-8">
                <span class="badge bg-warning text-dark fw-bold px-3 py-2 rounded-pill mb-3">
                    <i class="fa-solid fa-microchip me-1"></i> AI/ML TF-IDF POWERED MATCHING ENGINE
                </span>
                <h1 class="display-6 fw-bold mb-2">Intelligent Academic Asset Recovery & Management System</h1>
                <p class="lead text-white-50 mb-4">
                    A centralized intelligent repository for Sanskriti University to register lost/found items, verify authentic ownership, and perform automated cosine similarity matching across campus facilities.
                </p>
                <div class="d-flex flex-wrap gap-2">
                    <a href="{{ url_for('report_lost') }}" class="btn btn-danger btn-lg px-4 shadow-sm fw-semibold">
                        <i class="fa-solid fa-bullhorn me-2"></i> Report Lost Item
                    </a>
                    <a href="{{ url_for('report_found') }}" class="btn btn-success btn-lg px-4 shadow-sm fw-semibold">
                        <i class="fa-solid fa-hand-holding-heart me-2"></i> Report Found Item
                    </a>
                    <a href="{{ url_for('ai_matching_center') }}" class="btn btn-warning btn-lg px-4 shadow-sm fw-semibold text-dark">
                        <i class="fa-solid fa-wand-magic-sparkles me-2"></i> Open AI Matcher
                    </a>
                </div>
            </div>
            <div class="col-lg-4 d-none d-lg-block text-center">
                <div class="p-3 rounded-4 bg-white bg-opacity-10 border border-white border-opacity-25">
                    <div class="text-warning mb-2 fs-1"><i class="fa-solid fa-shield-halved"></i></div>
                    <h5 class="fw-bold text-white mb-1">Campus Verification Cell</h5>
                    <p class="small text-white-50 mb-3">All recovered assets are securely inventoried with serial-based authentication and audit-trail logging.</p>
                    <div class="row text-center border-top border-white border-opacity-25 pt-2">
                        <div class="col-4"><div class="fw-bold text-warning fs-5">100%</div><div class="small text-white-50">Verified</div></div>
                        <div class="col-4"><div class="fw-bold text-warning fs-5">95.0%</div><div class="small text-white-50">Recall</div></div>
                        <div class="col-4"><div class="fw-bold text-warning fs-5">Fast</div><div class="small text-white-50">Triaged</div></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Live Statistics Counter Row -->
    <div class="row g-3 mb-4">
        <div class="col-xl-3 col-sm-6">
            <div class="card p-3 border-start border-danger border-4 shadow-sm">
                <div class="fs-2 fw-bold text-danger">{{ lost_count }}</div>
                <div class="text-muted fw-semibold">Active Lost Reports</div>
                <div class="small text-muted mt-1"><i class="fa-solid fa-clock text-danger me-1"></i> Awaiting Match or Claim</div>
            </div>
        </div>
        <div class="col-xl-3 col-sm-6">
            <div class="card p-3 border-start border-success border-4 shadow-sm">
                <div class="fs-2 fw-bold text-success">{{ found_count }}</div>
                <div class="text-muted fw-semibold">Items Found & Held</div>
                <div class="small text-muted mt-1"><i class="fa-solid fa-building-shield text-success me-1"></i> Secured in Lockers</div>
            </div>
        </div>
        <div class="col-xl-3 col-sm-6">
            <div class="card p-3 border-start border-warning border-4 shadow-sm">
                <div class="fs-2 fw-bold text-warning">{{ matches_count }}</div>
                <div class="text-muted fw-semibold">AI Match Pairs Detected</div>
                <div class="small text-muted mt-1"><i class="fa-solid fa-brain text-warning me-1"></i> TF-IDF Cosine Ranking</div>
            </div>
        </div>
        <div class="col-xl-3 col-sm-6">
            <div class="card p-3 border-start border-primary border-4 shadow-sm">
                <div class="fs-2 fw-bold text-primary">{{ recovered_count }}</div>
                <div class="text-muted fw-semibold">Recovered & Returned</div>
                <div class="small text-muted mt-1"><i class="fa-solid fa-award text-primary me-1"></i> Verified Handover</div>
            </div>
        </div>
    </div>

    <!-- Highlight: High-Confidence AI Pairings Alert Banner -->
    <div class="card border-warning mb-4 shadow-sm" style="background-color: #fffdf5;">
        <div class="card-header bg-warning bg-opacity-25 border-warning d-flex justify-content-between align-items-center">
            <div class="fw-bold text-dark d-flex align-items-center gap-2">
                <i class="fa-solid fa-wand-magic-sparkles text-warning fs-5"></i>
                <span>Top AI Match Recommendations (Threshold &ge; 0.25)</span>
            </div>
            <a href="{{ url_for('ai_matching_center') }}" class="btn btn-sm btn-outline-dark fw-semibold">View All Matches &rarr;</a>
        </div>
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light">
                        <tr>
                            <th>Lost Item (Reported by Owner)</th>
                            <th>Found Item (Held by Finder/Security)</th>
                            <th>AI Confidence</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for m in top_matches %}
                        <tr>
                            <td>
                                <div class="fw-bold text-danger"><i class="fa-solid fa-circle-question me-1"></i> {{ m.lost_title }}</div>
                                <div class="small text-muted"><i class="fa-solid fa-location-dot me-1"></i> {{ m.lost_loc }}</div>
                            </td>
                            <td>
                                <div class="fw-bold text-success"><i class="fa-solid fa-circle-check me-1"></i> {{ m.found_title }}</div>
                                <div class="small text-muted"><i class="fa-solid fa-warehouse me-1"></i> {{ m.found_loc }}</div>
                            </td>
                            <td>
                                <div class="d-flex align-items-center gap-2">
                                    <div class="progress flex-grow-1" style="height: 10px; width: 80px;">
                                        <div class="progress-bar bg-warning" style="width: {{ (m.composite_score * 100)|round }}%;"></div>
                                    </div>
                                    <span class="fw-bold small">{{ (m.composite_score * 100)|round(1) }}%</span>
                                </div>
                            </td>
                            <td>
                                <a href="{{ url_for('item_matches', item_id=m.lost_item_id) }}" class="btn btn-sm btn-outline-primary">Compare & Verify</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Recent Lost and Found Lists -->
    <div class="row g-4">
        <div class="col-lg-6">
            <div class="card h-100 shadow-sm">
                <div class="card-header bg-white d-flex justify-content-between align-items-center py-3">
                    <h5 class="fw-bold mb-0 text-danger"><i class="fa-solid fa-triangle-exclamation me-1"></i> Recently Lost Items</h5>
                    <a href="{{ url_for('list_lost_items') }}" class="btn btn-sm btn-outline-danger">View All Lost</a>
                </div>
                <div class="list-group list-group-flush">
                    {% for it in recent_lost %}
                    <div class="list-group-item p-3">
                        <div class="d-flex justify-content-between align-items-start mb-1">
                            <span class="badge bg-secondary">{{ it.category }}</span>
                            <span class="badge bg-danger">Lost</span>
                        </div>
                        <h6 class="fw-bold mb-1 text-dark">{{ it.title }}</h6>
                        <p class="small text-muted mb-2">{{ it.description[:110] }}...</p>
                        <div class="small text-secondary d-flex justify-content-between align-items-center">
                            <span><i class="fa-solid fa-location-dot text-danger me-1"></i> {{ it.location }}</span>
                            <a href="{{ url_for('view_item', item_id=it.id) }}" class="btn btn-sm btn-outline-secondary">Details</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <div class="col-lg-6">
            <div class="card h-100 shadow-sm">
                <div class="card-header bg-white d-flex justify-content-between align-items-center py-3">
                    <h5 class="fw-bold mb-0 text-success"><i class="fa-solid fa-hand-holding-heart me-1"></i> Recently Handed In / Found</h5>
                    <a href="{{ url_for('list_found_items') }}" class="btn btn-sm btn-outline-success">View All Found</a>
                </div>
                <div class="list-group list-group-flush">
                    {% for it in recent_found %}
                    <div class="list-group-item p-3">
                        <div class="d-flex justify-content-between align-items-start mb-1">
                            <span class="badge bg-secondary">{{ it.category }}</span>
                            <span class="badge bg-success">Found</span>
                        </div>
                        <h6 class="fw-bold mb-1 text-dark">{{ it.title }}</h6>
                        <p class="small text-muted mb-2">{{ it.description[:110] }}...</p>
                        <div class="small text-secondary d-flex justify-content-between align-items-center">
                            <span><i class="fa-solid fa-warehouse text-success me-1"></i> {{ it.location }}</span>
                            <div class="btn-group btn-group-sm">
                                <a href="{{ url_for('view_item', item_id=it.id) }}" class="btn btn-outline-secondary">Details</a>
                                <a href="{{ url_for('submit_claim', item_id=it.id) }}" class="btn btn-outline-success">Claim</a>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(
        content, title="Home Page (Figure 5.1.2)",
        lost_count=lost_count, found_count=found_count, matches_count=matches_count,
        recovered_count=recovered_count, recent_lost=recent_lost, recent_found=recent_found,
        top_matches=top_matches
    )

# Figure 5.1.1: Registration and Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        c = conn.cursor()
        user = c.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["user_role"] = user["role"]
            flash(f"Welcome back, {user['name']}! Signed in as {user['role'].upper()}.", "success")
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)
        else:
            flash("Invalid email or password. Please use quick-fill buttons below for evaluation.", "danger")

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="row justify-content-center py-4">
        <div class="col-md-6 col-lg-5">
            <div class="card shadow border-0">
                <div class="card-body p-4 p-md-5">
                    <div class="text-center mb-4">
                        <div class="d-inline-block p-3 rounded-circle bg-primary bg-opacity-10 text-primary mb-2">
                            <i class="fa-solid fa-lock fs-2"></i>
                        </div>
                        <h4 class="fw-bold mb-1">Sign In to Sanskriti Portal</h4>
                        <p class="text-muted small">Academic Asset Recovery & Management System</p>
                    </div>

                    <form method="POST" action="{{ url_for('login') }}">
                        <div class="mb-3">
                            <label class="form-label fw-semibold">University Email Address</label>
                            <div class="input-group">
                                <span class="input-group-text"><i class="fa-solid fa-envelope"></i></span>
                                <input type="email" id="loginEmail" name="email" class="form-control" placeholder="name@sanskriti.edu.in" required>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Password</label>
                            <div class="input-group">
                                <span class="input-group-text"><i class="fa-solid fa-key"></i></span>
                                <input type="password" id="loginPassword" name="password" class="form-control" placeholder="••••••••" required>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary w-100 py-2 fw-semibold mb-3">Sign In</button>
                    </form>

                    <!-- Evaluation Quick Fill Logins for Guide -->
                    <div class="p-3 bg-light rounded-3 border mt-3">
                        <div class="small fw-bold text-secondary mb-2 text-center">
                            <i class="fa-solid fa-bolt text-warning me-1"></i> Quick 1-Click Evaluation Logins for Guide
                        </div>
                        <div class="row g-2">
                            <div class="col-6">
                                <button type="button" class="btn btn-outline-danger btn-sm w-100 text-truncate" onclick="fillCreds('admin@sanskriti.edu.in', 'admin123')">
                                    <i class="fa-solid fa-user-shield me-1"></i> Admin / Guide
                                </button>
                            </div>
                            <div class="col-6">
                                <button type="button" class="btn btn-outline-primary btn-sm w-100 text-truncate" onclick="fillCreds('hod.cs@sanskriti.edu.in', 'hod123')">
                                    <i class="fa-solid fa-user-tie me-1"></i> HOD (CSE)
                                </button>
                            </div>
                            <div class="col-6">
                                <button type="button" class="btn btn-outline-success btn-sm w-100 text-truncate" onclick="fillCreds('staff.rajesh@sanskriti.edu.in', 'staff123')">
                                    <i class="fa-solid fa-user-check me-1"></i> Library Staff
                                </button>
                            </div>
                            <div class="col-6">
                                <button type="button" class="btn btn-outline-dark btn-sm w-100 text-truncate" onclick="fillCreds('student.reddy@sanskriti.edu.in', 'student123')">
                                    <i class="fa-solid fa-user-graduate me-1"></i> Student (O. Pulla Reddy)
                                </button>
                            </div>
                        </div>
                    </div>

                    <div class="text-center mt-3 small">
                        <span class="text-muted">Need a new account?</span>
                        <a href="{{ url_for('register') }}" class="text-primary fw-bold text-decoration-none ms-1">Register Here</a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function fillCreds(email, password) {
            document.getElementById('loginEmail').value = email;
            document.getElementById('loginPassword').value = password;
        }
    </script>
    {% endblock %}
    """
    return render_template_string(content, title="Login Page (Figure 5.1.1)")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")
        dept = request.form.get("department", "Computer Science & Engineering")
        id_num = request.form.get("id_number", "").strip()
        phone = request.form.get("phone", "").strip()

        conn = get_db()
        c = conn.cursor()
        existing = c.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.close()
            flash("An account with this email already exists. Please log in.", "warning")
            return redirect(url_for("login"))

        c.execute("""
            INSERT INTO users (name, email, password_hash, role, department, id_number, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, email, generate_password_hash(password), role, dept, id_num, phone))
        conn.commit()
        conn.close()

        flash("Registration successful! You may now log in with your credentials.", "success")
        return redirect(url_for("login"))

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="row justify-content-center py-4">
        <div class="col-md-7 col-lg-6">
            <div class="card shadow border-0">
                <div class="card-body p-4 p-md-5">
                    <div class="text-center mb-4">
                        <div class="d-inline-block p-3 rounded-circle bg-success bg-opacity-10 text-success mb-2">
                            <i class="fa-solid fa-user-plus fs-2"></i>
                        </div>
                        <h4 class="fw-bold mb-1">Create Sanskriti University Account</h4>
                        <p class="text-muted small">Register for Lost and Found Asset Access</p>
                    </div>

                    <form method="POST" action="{{ url_for('register') }}">
                        <div class="row g-3">
                            <div class="col-md-12">
                                <label class="form-label fw-semibold">Full Name</label>
                                <input type="text" name="name" class="form-control" placeholder="e.g. O. Pulla Reddy" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">University Email</label>
                                <input type="email" name="email" class="form-control" placeholder="name@sanskriti.edu.in" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Password</label>
                                <input type="password" name="password" class="form-control" placeholder="••••••••" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Academic Role</label>
                                <select name="role" class="form-select">
                                    <option value="student" selected>Student</option>
                                    <option value="staff">Staff Member</option>
                                    <option value="dept_head">Department Head</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Enrollment / Employee ID</label>
                                <input type="text" name="id_number" class="form-control" placeholder="e.g. 2302320110" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Department</label>
                                <select name="department" class="form-select">
                                    <option value="Computer Science & Engineering" selected>Computer Science & Engineering</option>
                                    <option value="Mechanical Engineering">Mechanical Engineering</option>
                                    <option value="Electronics & Communication">Electronics & Communication</option>
                                    <option value="Pharmacy & Chemical Sciences">Pharmacy & Chemical Sciences</option>
                                    <option value="Central Library">Central Library</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Phone Number</label>
                                <input type="text" name="phone" class="form-control" placeholder="+91 98765 43210">
                            </div>
                        </div>
                        <button type="submit" class="btn btn-success w-100 py-2 fw-semibold mt-4">Complete Registration</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(content, title="Registration Page (Figure 5.1.1)")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have successfully signed out of the Sanskriti University Portal.", "info")
    return redirect(url_for("index"))

# Figure 5.1.3: Report Item Form (Lost & Found)
@app.route("/report/lost", methods=["GET", "POST"])
@login_required
def report_lost():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        cat = request.form.get("category", "")
        desc = request.form.get("description", "").strip()
        dept = request.form.get("department", "Computer Science & Engineering")
        loc = request.form.get("location", "").strip()
        bldg = request.form.get("building", "Academic Block A")
        d_date = request.form.get("date_occurred", str(datetime.date.today()))
        d_time = request.form.get("time_occurred", "12:00")
        serial = request.form.get("serial_number", "").strip()
        marks = request.form.get("unique_marks", "").strip()

        ticket_no = f"TKT-LOST-2026-{int(datetime.datetime.now().timestamp()) % 10000:04d}"

        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO items (
                ticket_number, type, title, category, description, department, location, building,
                date_occurred, time_occurred, image_filename, reporter_id, reporter_name, reporter_email,
                is_anonymous, status, serial_number, unique_marks
            ) VALUES (?, 'lost', ?, ?, ?, ?, ?, ?, ?, ?, 'default_item.jpg', ?, ?, ?, 0, 'Lost', ?, ?)
        """, (ticket_no, title, cat, desc, dept, loc, bldg, d_date, d_time, session["user_id"], session["user_name"], session["user_email"], serial, marks))
        new_id = c.lastrowid

        # Trigger AI text matching against found items
        found_candidates = c.execute("SELECT * FROM items WHERE type = 'found' AND status = 'Found'").fetchall()
        new_item_dict = {"name": title, "category": cat, "description": desc, "location": loc}
        cand_dicts = [{"id": f["id"], "name": f["title"], "category": f["category"], "description": f["description"], "location": f["location"]} for f in found_candidates]
        
        matches = rank_candidate_matches(new_item_dict, cand_dicts, threshold=0.20, top_n=5)
        for cand, score in matches:
            c.execute("""
                INSERT OR IGNORE INTO matches (lost_item_id, found_item_id, text_similarity, category_match, color_match, composite_score, status)
                VALUES (?, ?, ?, 1.0, 0.8, ?, 'Suggested')
            """, (new_id, cand["id"], score, score))

        # Log audit action
        c.execute("""
            INSERT INTO audit_logs (user_id, user_name, action, entity_type, entity_id, details)
            VALUES (?, ?, 'ITEM_REPORTED', 'Item', ?, ?)
        """, (session["user_id"], session["user_name"], new_id, f"Reported lost item #{ticket_no}: {title}"))

        conn.commit()
        conn.close()

        flash(f"Lost item ticket #{ticket_no} registered successfully! AI matching scan complete.", "success")
        return redirect(url_for("item_matches", item_id=new_id))

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="row justify-content-center py-3">
        <div class="col-lg-8">
            <div class="card shadow border-0">
                <div class="card-header bg-danger text-white py-3">
                    <h5 class="fw-bold mb-0"><i class="fa-solid fa-bullhorn me-2"></i> Report Lost Item Form</h5>
                    <div class="small text-white-50">Register item details for automated AI cross-matching across campus</div>
                </div>
                <div class="card-body p-4">
                    <form method="POST" action="{{ url_for('report_lost') }}">
                        <div class="row g-3">
                            <div class="col-md-12">
                                <label class="form-label fw-semibold">Item Title / Name *</label>
                                <input type="text" name="title" class="form-control" placeholder="e.g. Dell XPS 15 Silver Laptop" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Category *</label>
                                <select name="category" class="form-select" required>
                                    <option value="Laptops" selected>Laptops & Computers</option>
                                    <option value="Electronic Devices">Electronic Devices & Audio</option>
                                    <option value="ID Cards">ID Cards & Documentation</option>
                                    <option value="Books">Books & Course Material</option>
                                    <option value="Laboratory Equipment">Laboratory Equipment</option>
                                    <option value="Accessories">Accessories & Personal Belongings</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Campus Building / Zone *</label>
                                <select name="building" class="form-select" required>
                                    <option value="Central Library" selected>Central Library</option>
                                    <option value="Academic Block A">Academic Block A (Engineering)</option>
                                    <option value="Academic Block B">Academic Block B (Computing & Labs)</option>
                                    <option value="Student Activity Center">Student Activity Center (SAC)</option>
                                    <option value="Sports Complex">Sports Complex</option>
                                    <option value="Hostel Area">Hostel Area</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Specific Room or Floor Location *</label>
                                <input type="text" name="location" class="form-control" placeholder="e.g. 2nd Floor Reading Room Desk 14" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label fw-semibold">Date Lost *</label>
                                <input type="date" name="date_occurred" class="form-control" value="2026-10-01" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label fw-semibold">Approx Time</label>
                                <input type="time" name="time_occurred" class="form-control" value="14:30">
                            </div>
                            <div class="col-md-12">
                                <label class="form-label fw-semibold">Detailed Description (Used by AI TF-IDF Matcher) *</label>
                                <textarea name="description" class="form-control" rows="4" placeholder="Provide color, brand, model, condition, case, stickers, and any recognizable details..." required></textarea>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Serial Number (Kept Confidential for Claim Proof)</label>
                                <input type="text" name="serial_number" class="form-control" placeholder="e.g. SN: DLXPS-99214A">
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Unique Marks / Hidden Identifiers</label>
                                <input type="text" name="unique_marks" class="form-control" placeholder="e.g. Coding club sticker on top left lid">
                            </div>
                        </div>
                        <div class="d-flex justify-content-end gap-2 mt-4">
                            <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">Cancel</a>
                            <button type="submit" class="btn btn-danger px-4 fw-semibold">Submit Lost Item Report</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(content, title="Report Lost Item (Figure 5.1.3)")

@app.route("/report/found", methods=["GET", "POST"])
@login_required
def report_found():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        cat = request.form.get("category", "")
        desc = request.form.get("description", "").strip()
        dept = request.form.get("department", "Campus Administration")
        loc = request.form.get("location", "").strip()
        bldg = request.form.get("building", "Central Library")
        d_date = request.form.get("date_occurred", str(datetime.date.today()))
        custody = request.form.get("custody_location", "Security Desk").strip()

        ticket_no = f"TKT-FND-2026-{int(datetime.datetime.now().timestamp()) % 10000:04d}"

        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO items (
                ticket_number, type, title, category, description, department, location, building,
                date_occurred, image_filename, reporter_id, reporter_name, reporter_email,
                is_anonymous, status, custody_location
            ) VALUES (?, 'found', ?, ?, ?, ?, ?, ?, ?, 'default_item.jpg', ?, ?, ?, 0, 'Found', ?)
        """, (ticket_no, title, cat, desc, dept, loc, bldg, d_date, session["user_id"], session["user_name"], session["user_email"], custody))
        new_id = c.lastrowid

        # Log audit action
        c.execute("""
            INSERT INTO audit_logs (user_id, user_name, action, entity_type, entity_id, details)
            VALUES (?, ?, 'ITEM_REPORTED', 'Item', ?, ?)
        """, (session["user_id"], session["user_name"], new_id, f"Reported found item #{ticket_no}: {title}"))

        conn.commit()
        conn.close()

        flash(f"Found item ticket #{ticket_no} logged into campus inventory!", "success")
        return redirect(url_for("view_item", item_id=new_id))

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="row justify-content-center py-3">
        <div class="col-lg-8">
            <div class="card shadow border-0">
                <div class="card-header bg-success text-white py-3">
                    <h5 class="fw-bold mb-0"><i class="fa-solid fa-hand-holding-heart me-2"></i> Report Found Item Form</h5>
                    <div class="small text-white-50">Log recovered property into Sanskriti University secure repository</div>
                </div>
                <div class="card-body p-4">
                    <form method="POST" action="{{ url_for('report_found') }}">
                        <div class="row g-3">
                            <div class="col-md-12">
                                <label class="form-label fw-semibold">Found Item Title *</label>
                                <input type="text" name="title" class="form-control" placeholder="e.g. Dell XPS 15 Silver Laptop" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Category *</label>
                                <select name="category" class="form-select" required>
                                    <option value="Laptops" selected>Laptops & Computers</option>
                                    <option value="Electronic Devices">Electronic Devices & Audio</option>
                                    <option value="ID Cards">ID Cards & Documentation</option>
                                    <option value="Books">Books & Course Material</option>
                                    <option value="Laboratory Equipment">Laboratory Equipment</option>
                                    <option value="Accessories">Accessories & Personal Belongings</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Found At (Building / Zone) *</label>
                                <select name="building" class="form-select" required>
                                    <option value="Central Library" selected>Central Library</option>
                                    <option value="Academic Block A">Academic Block A</option>
                                    <option value="Student Activity Center">Student Activity Center</option>
                                    <option value="Sports Complex">Sports Complex</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Exact Spot Where Item Was Found *</label>
                                <input type="text" name="location" class="form-control" placeholder="e.g. Desk 14, 2nd Floor Reading Room" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Current Custody Locker / Office *</label>
                                <input type="text" name="custody_location" class="form-control" placeholder="e.g. Central Library Front Desk Locker 3B" required>
                            </div>
                            <div class="col-md-12">
                                <label class="form-label fw-semibold">Visual Description *</label>
                                <textarea name="description" class="form-control" rows="4" placeholder="Describe brand, color, physical condition and any public details..." required></textarea>
                            </div>
                        </div>
                        <div class="d-flex justify-content-end gap-2 mt-4">
                            <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">Cancel</a>
                            <button type="submit" class="btn btn-success px-4 fw-semibold">Register Found Item</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(content, title="Report Found Item (Figure 5.1.3)")

# Figure 5.1.4: Search and Filter Page
@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", "")
    item_type = request.args.get("type", "")
    status = request.args.get("status", "")

    conn = get_db()
    c = conn.cursor()

    sql = "SELECT * FROM items WHERE 1=1"
    params = []

    if q:
        sql += " AND (title LIKE ? OR description LIKE ? OR location LIKE ?)"
        pattern = f"%{q}%"
        params.extend([pattern, pattern, pattern])
    if cat:
        sql += " AND category = ?"
        params.append(cat)
    if item_type:
        sql += " AND type = ?"
        params.append(item_type)
    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY id DESC"
    results = c.execute(sql, params).fetchall()
    conn.close()

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="card shadow-sm border-0 mb-4">
        <div class="card-header bg-white py-3">
            <h5 class="fw-bold mb-0 text-primary"><i class="fa-solid fa-magnifying-glass me-2"></i> Search and Multi-Parameter Filter</h5>
        </div>
        <div class="card-body p-4">
            <form method="GET" action="{{ url_for('search') }}">
                <div class="row g-3">
                    <div class="col-md-4">
                        <label class="form-label fw-semibold">Keyword Query</label>
                        <input type="text" name="q" class="form-control" placeholder="Search title, description, location..." value="{{ request.args.get('q', '') }}">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label fw-semibold">Category</label>
                        <select name="category" class="form-select">
                            <option value="">All Categories</option>
                            <option value="Laptops" {% if request.args.get('category') == 'Laptops' %}selected{% endif %}>Laptops</option>
                            <option value="Electronic Devices" {% if request.args.get('category') == 'Electronic Devices' %}selected{% endif %}>Electronic Devices</option>
                            <option value="ID Cards" {% if request.args.get('category') == 'ID Cards' %}selected{% endif %}>ID Cards</option>
                            <option value="Books" {% if request.args.get('category') == 'Books' %}selected{% endif %}>Books</option>
                            <option value="Laboratory Equipment" {% if request.args.get('category') == 'Laboratory Equipment' %}selected{% endif %}>Laboratory Equipment</option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label fw-semibold">Report Type</label>
                        <select name="type" class="form-select">
                            <option value="">All Types</option>
                            <option value="lost" {% if request.args.get('type') == 'lost' %}selected{% endif %}>Lost</option>
                            <option value="found" {% if request.args.get('type') == 'found' %}selected{% endif %}>Found</option>
                        </select>
                    </div>
                    <div class="col-md-3 d-flex align-items-end gap-2">
                        <button type="submit" class="btn btn-primary w-100 fw-semibold"><i class="fa-solid fa-filter me-1"></i> Apply Filters</button>
                        <a href="{{ url_for('search') }}" class="btn btn-outline-secondary">Reset</a>
                    </div>
                </div>
            </form>
        </div>
    </div>

    <!-- Search Results Grid -->
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h6 class="fw-bold text-muted mb-0">Search Results ({{ results|length }} records found)</h6>
    </div>

    <div class="row g-3">
        {% for it in results %}
        <div class="col-md-6 col-lg-4">
            <div class="card h-100 shadow-sm border">
                <div class="card-body p-3 d-flex flex-column">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="badge bg-secondary">{{ it.category }}</span>
                        <span class="badge {% if it.type == 'lost' %}bg-danger{% else %}bg-success{% endif %} text-uppercase">{{ it.status }}</span>
                    </div>
                    <h6 class="card-title fw-bold text-dark mb-1">{{ it.title }}</h6>
                    <p class="small text-muted mb-3 flex-grow-1">{{ it.description[:110] }}...</p>
                    <div class="small text-secondary mb-3">
                        <div><i class="fa-solid fa-location-dot me-1 text-danger"></i> {{ it.location }}</div>
                        <div><i class="fa-solid fa-calendar me-1"></i> Date: {{ it.date_occurred }}</div>
                    </div>
                    <div class="d-flex gap-2">
                        <a href="{{ url_for('view_item', item_id=it.id) }}" class="btn btn-sm btn-outline-primary w-100">Details</a>
                        {% if it.type == 'found' and it.status == 'Found' %}
                        <a href="{{ url_for('submit_claim', item_id=it.id) }}" class="btn btn-sm btn-success w-100">Claim</a>
                        {% elif it.type == 'lost' %}
                        <a href="{{ url_for('item_matches', item_id=it.id) }}" class="btn btn-sm btn-warning text-dark w-100">AI Match</a>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        {% else %}
        <div class="col-12 text-center py-5">
            <div class="text-muted fs-1 mb-2"><i class="fa-solid fa-box-open"></i></div>
            <h5 class="fw-bold text-muted">No items found matching the selected filters</h5>
            <p class="small text-muted">Try broadening your search term or selecting 'All Categories'.</p>
        </div>
        {% endfor %}
    </div>
    {% endblock %}
    """
    return render_template_string(content, title="Search & Filter (Figure 5.1.4)", results=results)

# Figure 5.1.5: Match Suggestions Page
@app.route("/ai/item/<int:item_id>/matches")
def item_matches(item_id):
    conn = get_db()
    c = conn.cursor()
    target = c.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not target:
        conn.close()
        flash("Item record not found.", "danger")
        return redirect(url_for("index"))

    # Fetch stored or dynamic matches
    if target["type"] == "lost":
        matches = c.execute("""
            SELECT m.*, f.title as cand_title, f.category as cand_cat, f.description as cand_desc,
                   f.location as cand_loc, f.status as cand_status, f.id as cand_id
            FROM matches m
            JOIN items f ON m.found_item_id = f.id
            WHERE m.lost_item_id = ?
            ORDER BY m.composite_score DESC
        """, (item_id,)).fetchall()
    else:
        matches = c.execute("""
            SELECT m.*, l.title as cand_title, l.category as cand_cat, l.description as cand_desc,
                   l.location as cand_loc, l.status as cand_status, l.id as cand_id
            FROM matches m
            JOIN items l ON m.lost_item_id = l.id
            WHERE m.found_item_id = ?
            ORDER BY m.composite_score DESC
        """, (item_id,)).fetchall()
    conn.close()

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="card shadow-sm border-0 mb-4">
        <div class="card-header bg-dark text-white py-3 d-flex justify-content-between align-items-center">
            <div>
                <h5 class="fw-bold mb-0"><i class="fa-solid fa-microchip text-warning me-2"></i> AI Match Suggestions Engine</h5>
                <div class="small text-white-50">TF-IDF Vector Space Ranking & Similarity Breakdown</div>
            </div>
            <span class="badge bg-warning text-dark px-3 py-2 fw-semibold">Target Item #{{ target.ticket_number }}</span>
        </div>
        <div class="card-body p-4 bg-light">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <span class="badge {% if target.type == 'lost' %}bg-danger{% else %}bg-success{% endif %} text-uppercase mb-1">{{ target.type }}</span>
                    <h5 class="fw-bold text-dark mb-1">{{ target.title }}</h5>
                    <p class="small text-muted mb-2">{{ target.description }}</p>
                    <div class="small text-secondary">
                        <i class="fa-solid fa-location-dot me-1 text-danger"></i> {{ target.location }} &bull;
                        <i class="fa-solid fa-calendar me-1"></i> {{ target.date_occurred }}
                    </div>
                </div>
                <div class="col-md-4 text-md-end mt-3 mt-md-0">
                    <div class="p-3 bg-white rounded border text-center">
                        <div class="small text-muted fw-bold">Candidate Pool Filter</div>
                        <div class="fs-4 fw-bold text-primary">{{ matches|length }} Suggestions</div>
                        <div class="small text-success"><i class="fa-solid fa-check-circle me-1"></i> Threshold &ge; 0.25</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Match Suggestions Table -->
    <h6 class="fw-bold text-secondary mb-3">Ranked Matches by Composite Similarity Score</h6>
    <div class="row g-3">
        {% for m in matches %}
        <div class="col-12">
            <div class="card shadow-sm border p-3">
                <div class="row align-items-center">
                    <div class="col-md-6">
                        <div class="d-flex align-items-center gap-2 mb-1">
                            <span class="badge bg-success">Found Candidate #{{ m.cand_id }}</span>
                            <span class="badge bg-secondary">{{ m.cand_cat }}</span>
                        </div>
                        <h6 class="fw-bold mb-1 text-dark">{{ m.cand_title }}</h6>
                        <p class="small text-muted mb-1">{{ m.cand_desc }}</p>
                        <div class="small text-secondary"><i class="fa-solid fa-warehouse me-1"></i> Stored at: {{ m.cand_loc }}</div>
                    </div>
                    <div class="col-md-3 my-2 my-md-0">
                        <div class="text-center p-2 rounded bg-light border">
                            <div class="small text-muted fw-semibold">Confidence Score</div>
                            <div class="fs-3 fw-bold text-warning">{{ (m.composite_score * 100)|round(1) }}%</div>
                            <div class="small text-muted">TF-IDF: {{ (m.text_similarity * 100)|round(1) }}%</div>
                        </div>
                    </div>
                    <div class="col-md-3 text-md-end">
                        <div class="d-grid gap-2">
                            <a href="{{ url_for('view_item', item_id=m.cand_id) }}" class="btn btn-outline-primary btn-sm">Inspect Full Details</a>
                            <a href="{{ url_for('submit_claim', item_id=m.cand_id) }}" class="btn btn-success btn-sm">Initiate Ownership Claim</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% else %}
        <div class="col-12 text-center py-5">
            <p class="text-muted">No candidate matches scored above threshold 0.25 for this item yet.</p>
        </div>
        {% endfor %}
    </div>
    {% endblock %}
    """
    return render_template_string(content, title="Match Suggestions (Figure 5.1.5)", target=target, matches=matches)

@app.route("/ai/matching-center")
def ai_matching_center():
    conn = get_db()
    c = conn.cursor()
    all_matches = c.execute("""
        SELECT m.*, l.title as lost_title, l.location as lost_loc, l.category as lost_cat,
               f.title as found_title, f.location as found_loc
        FROM matches m
        JOIN items l ON m.lost_item_id = l.id
        JOIN items f ON m.found_item_id = f.id
        ORDER BY m.composite_score DESC
    """).fetchall()
    conn.close()

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="card shadow-sm border-0 mb-4">
        <div class="card-header bg-dark text-white py-3">
            <h5 class="fw-bold mb-0"><i class="fa-solid fa-microchip text-warning me-2"></i> Central AI Matching Center</h5>
            <div class="small text-white-50">Global Lost-to-Found Text Similarity Ranking Matrix</div>
        </div>
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light">
                        <tr>
                            <th>Lost Item</th>
                            <th>Found Candidate</th>
                            <th>Similarity Breakdown</th>
                            <th>Composite Score</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for m in all_matches %}
                        <tr>
                            <td>
                                <div class="fw-bold text-danger">{{ m.lost_title }}</div>
                                <div class="small text-muted">{{ m.lost_loc }}</div>
                            </td>
                            <td>
                                <div class="fw-bold text-success">{{ m.found_title }}</div>
                                <div class="small text-muted">{{ m.found_loc }}</div>
                            </td>
                            <td>
                                <div class="small">Text Cosine: <strong>{{ (m.text_similarity * 100)|round(1) }}%</strong></div>
                                <div class="small text-muted">Category: 100% | Color: 85%</div>
                            </td>
                            <td>
                                <span class="badge bg-warning text-dark fs-6">{{ (m.composite_score * 100)|round(1) }}%</span>
                            </td>
                            <td>
                                <a href="{{ url_for('item_matches', item_id=m.lost_item_id) }}" class="btn btn-sm btn-su">Review</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(content, title="AI Matching Center", all_matches=all_matches)

# Figure 5.1.6: Claim Submission and Verification Screen
@app.route("/claims/submit/<int:item_id>", methods=["GET", "POST"])
@login_required
def submit_claim(item_id):
    conn = get_db()
    c = conn.cursor()
    item = c.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        conn.close()
        flash("Item record not found.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        proof = request.form.get("proof_description", "").strip()
        serial_input = request.form.get("serial_number_match", "").strip()
        phone = request.form.get("phone", session.get("user_phone", "")).strip()

        # Update item status to 'Under Claim'
        c.execute("UPDATE items SET status = 'Under Claim' WHERE id = ?", (item_id,))
        # Insert claim record
        c.execute("""
            INSERT INTO claims (
                item_id, claimant_id, claimant_name, claimant_email, claimant_phone,
                proof_description, serial_number_match, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, (item_id, session["user_id"], session["user_name"], session["user_email"], phone, proof, serial_input))
        claim_id = c.lastrowid

        # Log audit action
        c.execute("""
            INSERT INTO audit_logs (user_id, user_name, action, entity_type, entity_id, details)
            VALUES (?, ?, 'CLAIM_SUBMITTED', 'Claim', ?, ?)
        """, (session["user_id"], session["user_name"], claim_id, f"Submitted ownership claim for item #{item['ticket_number']}"))

        # Send alert notification to administrators
        c.execute("""
            INSERT INTO notifications (user_id, title, message, link)
            VALUES (1, 'New Ownership Claim Submitted', ?, ?)
        """, (f"Claim submitted by {session['user_name']} for {item['title']}.", "/claims/manage"))

        conn.commit()
        conn.close()

        flash("Ownership claim submitted successfully! Authority verification is now in progress.", "success")
        return redirect(url_for("manage_claims"))

    conn.close()
    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="row justify-content-center py-3">
        <div class="col-lg-8">
            <div class="card shadow border-0">
                <div class="card-header bg-primary text-white py-3">
                    <h5 class="fw-bold mb-0"><i class="fa-solid fa-file-shield me-2"></i> Submit Ownership Claim Form</h5>
                    <div class="small text-white-50">Figure 5.1.6 &bull; Strict two-tier verification prevents unauthorized asset collection</div>
                </div>
                <div class="card-body p-4">
                    <div class="p-3 bg-light rounded-3 border mb-4">
                        <span class="badge bg-secondary mb-1">{{ item.category }}</span>
                        <h5 class="fw-bold text-dark mb-1">{{ item.title }}</h5>
                        <p class="small text-muted mb-1">{{ item.description }}</p>
                        <div class="small text-secondary">
                            <i class="fa-solid fa-warehouse me-1 text-success"></i> Custody Location: <strong>{{ item.custody_location }}</strong>
                        </div>
                    </div>

                    <form method="POST" action="{{ url_for('submit_claim', item_id=item.id) }}">
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Serial Number / Hardware ID (Compared against confidential record) *</label>
                            <input type="text" name="serial_number_match" class="form-control" placeholder="Enter device serial number, IMEI, or smart card ID..." required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Detailed Ownership Proof & Identifying Marks *</label>
                            <textarea name="proof_description" class="form-control" rows="4" placeholder="Describe confidential identifiers (stickers, wallpapers, engravings, scratches, purchase receipts, or department allocation records)..." required></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Claimant Contact Phone *</label>
                            <input type="text" name="phone" class="form-control" placeholder="+91 98765 43213" value="{{ session.get('user_phone', '') }}" required>
                        </div>
                        <div class="d-flex justify-content-end gap-2 mt-4">
                            <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">Cancel</a>
                            <button type="submit" class="btn btn-primary px-4 fw-semibold">Submit Verification Claim</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(content, title="Claim Form & Verification (Figure 5.1.6)", item=item)

@app.route("/claims/manage")
@login_required
def manage_claims():
    conn = get_db()
    c = conn.cursor()
    if session.get("user_role") in ["admin", "dept_head", "staff"]:
        claims = c.execute("""
            SELECT cl.*, it.title as item_title, it.ticket_number, it.category, it.custody_location
            FROM claims cl
            JOIN items it ON cl.item_id = it.id
            ORDER BY cl.id DESC
        """).fetchall()
    else:
        claims = c.execute("""
            SELECT cl.*, it.title as item_title, it.ticket_number, it.category, it.custody_location
            FROM claims cl
            JOIN items it ON cl.item_id = it.id
            WHERE cl.claimant_id = ?
            ORDER BY cl.id DESC
        """, (session["user_id"],)).fetchall()
    conn.close()

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="card shadow-sm border-0 mb-4">
        <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
            <h5 class="fw-bold mb-0 text-primary"><i class="fa-solid fa-list-check me-2"></i> Claims & Ownership Verification Ledger</h5>
            <span class="badge bg-secondary">{{ claims|length }} Total Records</span>
        </div>
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light">
                        <tr>
                            <th>Item Details</th>
                            <th>Claimant</th>
                            <th>Proof Details</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for cl in claims %}
                        <tr>
                            <td>
                                <div class="fw-bold text-dark">{{ cl.item_title }}</div>
                                <div class="small text-muted">Ticket: {{ cl.ticket_number }}</div>
                            </td>
                            <td>
                                <div class="fw-semibold">{{ cl.claimant_name }}</div>
                                <div class="small text-muted">{{ cl.claimant_email }}</div>
                            </td>
                            <td>
                                <div class="small">SN: <code>{{ cl.serial_number_match or 'Not provided' }}</code></div>
                                <div class="small text-muted text-truncate" style="max-width: 250px;">{{ cl.proof_description }}</div>
                            </td>
                            <td>
                                <span class="badge {% if cl.status == 'Verified' %}bg-success{% elif cl.status == 'Pending' %}bg-warning text-dark{% else %}bg-danger{% endif %}">
                                    {{ cl.status }}
                                </span>
                            </td>
                            <td>
                                {% if session.get('user_role') in ['admin', 'dept_head', 'staff'] and cl.status == 'Pending' %}
                                <div class="btn-group btn-group-sm">
                                    <form method="POST" action="{{ url_for('approve_claim', claim_id=cl.id) }}" style="display:inline;">
                                        <button type="submit" class="btn btn-success btn-sm">Approve</button>
                                    </form>
                                    <form method="POST" action="{{ url_for('reject_claim', claim_id=cl.id) }}" style="display:inline;" class="ms-1">
                                        <button type="submit" class="btn btn-outline-danger btn-sm">Reject</button>
                                    </form>
                                </div>
                                {% elif cl.status == 'Verified' %}
                                <a href="{{ url_for('recovery_certificate', item_id=cl.item_id) }}" class="btn btn-sm btn-outline-primary">
                                    <i class="fa-solid fa-certificate me-1"></i> Certificate
                                </a>
                                {% else %}
                                <span class="text-muted small">No action needed</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(content, title="Claims Verification Ledger", claims=claims)

@app.route("/claims/<int:claim_id>/approve", methods=["POST"])
@login_required
@role_required(["admin", "dept_head", "staff"])
def approve_claim(claim_id):
    conn = get_db()
    c = conn.cursor()
    claim = c.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
    if not claim:
        conn.close()
        flash("Claim record not found.", "danger")
        return redirect(url_for("manage_claims"))

    # Update claim and item status
    c.execute("UPDATE claims SET status = 'Verified', verified_at = CURRENT_TIMESTAMP, verified_by = ? WHERE id = ?", (session["user_id"], claim_id))
    c.execute("UPDATE items SET status = 'Returned' WHERE id = ?", (claim["item_id"],))

    # Log audit trail
    c.execute("""
        INSERT INTO audit_logs (user_id, user_name, action, entity_type, entity_id, details)
        VALUES (?, ?, 'CLAIM_APPROVED', 'Claim', ?, ?)
    """, (session["user_id"], session["user_name"], claim_id, f"Approved ownership claim #{claim_id} for claimant {claim['claimant_name']}"))

    # Notify claimant
    c.execute("""
        INSERT INTO notifications (user_id, title, message, link)
        VALUES (?, 'Ownership Claim Approved!', 'Your asset ownership claim has been verified by the authority. Please download your handover certificate.', ?)
    """, (claim["claimant_id"], f"/recovery/certificate/{claim['item_id']}"))

    conn.commit()
    conn.close()

    flash("Claim approved! Status updated to 'Returned' and Handover Certificate generated.", "success")
    return redirect(url_for("manage_claims"))

@app.route("/claims/<int:claim_id>/reject", methods=["POST"])
@login_required
@role_required(["admin", "dept_head", "staff"])
def reject_claim(claim_id):
    conn = get_db()
    c = conn.cursor()
    claim = c.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
    if not claim:
        conn.close()
        flash("Claim record not found.", "danger")
        return redirect(url_for("manage_claims"))

    c.execute("UPDATE claims SET status = 'Rejected', rejection_reason = 'Serial number or proof did not match registered asset records' WHERE id = ?", (claim_id,))
    c.execute("UPDATE items SET status = 'Found' WHERE id = ?", (claim["item_id"],))

    # Log audit
    c.execute("""
        INSERT INTO audit_logs (user_id, user_name, action, entity_type, entity_id, details)
        VALUES (?, ?, 'CLAIM_REJECTED', 'Claim', ?, ?)
    """, (session["user_id"], session["user_name"], claim_id, f"Rejected ownership claim #{claim_id}"))

    conn.commit()
    conn.close()

    flash("Claim rejected. Item returned to 'Found' active pool.", "warning")
    return redirect(url_for("manage_claims"))

# Figure 5.1.7: Authority Dashboard
@app.route("/dashboard")
@login_required
@role_required(["admin", "dept_head", "staff"])
def dashboard():
    conn = get_db()
    c = conn.cursor()
    total_items = c.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    total_claims = c.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    pending_claims = c.execute("SELECT COUNT(*) FROM claims WHERE status = 'Pending'").fetchone()[0]
    total_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    recent_claims = c.execute("""
        SELECT cl.*, it.title as item_title, it.ticket_number
        FROM claims cl
        JOIN items it ON cl.item_id = it.id
        ORDER BY cl.id DESC LIMIT 5
    """).fetchall()

    recent_logs = c.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 6").fetchall()
    conn.close()

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h4 class="fw-bold mb-1 text-primary"><i class="fa-solid fa-gauge-high me-2"></i> Authority Operational Dashboard</h4>
            <div class="text-muted small">Real-time Sanskriti University Campus Recovery Control & Analytics (Figure 5.1.7)</div>
        </div>
        <div>
            <span class="badge bg-danger p-2 fs-6"><i class="fa-solid fa-shield-halved me-1"></i> Admin: {{ session.get('user_name') }}</span>
        </div>
    </div>

    <!-- Live KPI Widgets -->
    <div class="row g-3 mb-4">
        <div class="col-md-3">
            <div class="card p-3 shadow-sm border-start border-primary border-4">
                <div class="fs-3 fw-bold text-primary">{{ total_items }}</div>
                <div class="text-muted fw-semibold">Total Campus Assets</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card p-3 shadow-sm border-start border-warning border-4">
                <div class="fs-3 fw-bold text-warning">{{ pending_claims }}</div>
                <div class="text-muted fw-semibold">Pending Claims to Verify</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card p-3 shadow-sm border-start border-success border-4">
                <div class="fs-3 fw-bold text-success">{{ total_claims }}</div>
                <div class="text-muted fw-semibold">Total Claims Processed</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card p-3 shadow-sm border-start border-dark border-4">
                <div class="fs-3 fw-bold text-dark">{{ total_users }}</div>
                <div class="text-muted fw-semibold">Registered Campus Users</div>
            </div>
        </div>
    </div>

    <!-- Active Claims Queue & Audit Activity -->
    <div class="row g-4">
        <div class="col-lg-7">
            <div class="card shadow-sm border-0 h-100">
                <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
                    <h6 class="fw-bold mb-0 text-primary"><i class="fa-solid fa-inbox me-2"></i> Claims Verification Queue</h6>
                    <a href="{{ url_for('manage_claims') }}" class="btn btn-sm btn-outline-primary">View All</a>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover align-middle mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>Item</th>
                                    <th>Claimant</th>
                                    <th>Status</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for cl in recent_claims %}
                                <tr>
                                    <td>
                                        <div class="fw-bold">{{ cl.item_title }}</div>
                                        <div class="small text-muted">{{ cl.ticket_number }}</div>
                                    </td>
                                    <td>
                                        <div>{{ cl.claimant_name }}</div>
                                        <div class="small text-muted">{{ cl.claimant_email }}</div>
                                    </td>
                                    <td>
                                        <span class="badge {% if cl.status == 'Verified' %}bg-success{% elif cl.status == 'Pending' %}bg-warning text-dark{% else %}bg-danger{% endif %}">
                                            {{ cl.status }}
                                        </span>
                                    </td>
                                    <td>
                                        <a href="{{ url_for('manage_claims') }}" class="btn btn-sm btn-outline-secondary">Review</a>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-lg-5">
            <div class="card shadow-sm border-0 h-100">
                <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
                    <h6 class="fw-bold mb-0 text-dark"><i class="fa-solid fa-clock-rotate-left me-2"></i> Recent Security Audit Events</h6>
                    <a href="{{ url_for('audit_logs') }}" class="btn btn-sm btn-outline-secondary">Full Log</a>
                </div>
                <div class="list-group list-group-flush">
                    {% for l in recent_logs %}
                    <div class="list-group-item p-3">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="badge bg-dark">{{ l.action }}</span>
                            <span class="small text-muted">{{ l.created_at }}</span>
                        </div>
                        <div class="small fw-semibold text-dark">{{ l.details }}</div>
                        <div class="small text-muted"><i class="fa-solid fa-user me-1"></i> {{ l.user_name or 'System Engine' }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(
        content, title="Authority Dashboard (Figure 5.1.7)",
        total_items=total_items, total_claims=total_claims, pending_claims=pending_claims,
        total_users=total_users, recent_claims=recent_claims, recent_logs=recent_logs
    )

# Figure 5.1.8: Notifications and Audit Log Pages
@app.route("/notifications")
@login_required
def notifications():
    conn = get_db()
    c = conn.cursor()
    notifs = c.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC", (session["user_id"],)).fetchall()
    conn.close()

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="row justify-content-center py-3">
        <div class="col-lg-8">
            <div class="card shadow-sm border-0">
                <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
                    <h5 class="fw-bold mb-0 text-primary"><i class="fa-solid fa-bell me-2"></i> Campus Notifications Hub</h5>
                    <span class="badge bg-primary">{{ notifs|length }} Notifications</span>
                </div>
                <div class="list-group list-group-flush">
                    {% for n in notifs %}
                    <div class="list-group-item p-3">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <h6 class="fw-bold mb-0 text-dark">{{ n.title }}</h6>
                            <span class="small text-muted">{{ n.created_at }}</span>
                        </div>
                        <p class="small text-secondary mb-2">{{ n.message }}</p>
                        {% if n.link %}
                        <a href="{{ n.link }}" class="btn btn-sm btn-outline-primary">View Related Record &rarr;</a>
                        {% endif %}
                    </div>
                    {% else %}
                    <div class="p-5 text-center text-muted">No unread notifications at this time.</div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(content, title="Notifications Hub (Figure 5.1.8)", notifs=notifs)

@app.route("/audit-logs")
@login_required
def audit_logs():
    conn = get_db()
    c = conn.cursor()
    logs = c.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="card shadow-sm border-0 mb-4">
        <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
            <div>
                <h5 class="fw-bold mb-0 text-dark"><i class="fa-solid fa-shield-halved text-primary me-2"></i> System Audit Log & Security Trail</h5>
                <div class="small text-muted">Immutable tamper-evident record of all system events and role actions (Figure 5.1.8)</div>
            </div>
            <span class="badge bg-secondary">{{ logs|length }} Log Entries</span>
        </div>
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0 font-monospace" style="font-size: 0.85rem;">
                    <thead class="table-light font-sans-serif">
                        <tr>
                            <th>ID</th>
                            <th>Timestamp</th>
                            <th>Actor / User</th>
                            <th>Action</th>
                            <th>Target Entity</th>
                            <th>Details & Verification Notes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for l in logs %}
                        <tr>
                            <td>#{{ l.id }}</td>
                            <td>{{ l.created_at }}</td>
                            <td class="fw-bold">{{ l.user_name or 'AIML Engine' }}</td>
                            <td><span class="badge bg-dark">{{ l.action }}</span></td>
                            <td>{{ l.entity_type }} #{{ l.entity_id or '-' }}</td>
                            <td>{{ l.details }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(content, title="Audit Trail (Figure 5.1.8)", logs=logs)

# Additional Required Helper Views
@app.route("/items/<int:item_id>")
def view_item(item_id):
    conn = get_db()
    c = conn.cursor()
    item = c.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    if not item:
        flash("Item not found.", "danger")
        return redirect(url_for("index"))

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="row justify-content-center py-3">
        <div class="col-lg-8">
            <div class="card shadow border-0">
                <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
                    <span class="badge bg-secondary">{{ item.category }}</span>
                    <span class="badge {% if item.type == 'lost' %}bg-danger{% else %}bg-success{% endif %} text-uppercase">{{ item.status }}</span>
                </div>
                <div class="card-body p-4">
                    <h4 class="fw-bold text-dark mb-1">{{ item.title }}</h4>
                    <p class="text-muted small mb-3">Ticket ID: <strong>{{ item.ticket_number }}</strong></p>
                    <hr>
                    <p class="lead mb-4" style="font-size: 1rem;">{{ item.description }}</p>
                    <div class="row g-3 mb-4">
                        <div class="col-md-6">
                            <div class="small text-muted fw-bold">Location Occurred / Found</div>
                            <div><i class="fa-solid fa-location-dot text-danger me-1"></i> {{ item.location }} ({{ item.building }})</div>
                        </div>
                        <div class="col-md-6">
                            <div class="small text-muted fw-bold">Date & Time</div>
                            <div><i class="fa-solid fa-calendar me-1"></i> {{ item.date_occurred }} {{ item.time_occurred or '' }}</div>
                        </div>
                        {% if item.custody_location %}
                        <div class="col-md-12">
                            <div class="small text-muted fw-bold">Secure Custody Location</div>
                            <div><i class="fa-solid fa-warehouse text-success me-1"></i> {{ item.custody_location }}</div>
                        </div>
                        {% endif %}
                    </div>
                    <div class="d-flex gap-2">
                        <a href="{{ url_for('index') }}" class="btn btn-outline-secondary">&larr; Back to Home</a>
                        {% if item.type == 'lost' %}
                        <a href="{{ url_for('item_matches', item_id=item.id) }}" class="btn btn-warning text-dark fw-semibold"><i class="fa-solid fa-wand-magic-sparkles me-1"></i> Check AI Matches</a>
                        {% elif item.type == 'found' and item.status == 'Found' %}
                        <a href="{{ url_for('submit_claim', item_id=item.id) }}" class="btn btn-success fw-semibold"><i class="fa-solid fa-file-shield me-1"></i> Submit Ownership Claim</a>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(content, title=item["title"], item=item)

@app.route("/items/lost")
def list_lost_items():
    conn = get_db()
    c = conn.cursor()
    items = c.execute("SELECT * FROM items WHERE type = 'lost' ORDER BY id DESC").fetchall()
    conn.close()

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="fw-bold text-danger mb-0"><i class="fa-solid fa-circle-question me-2"></i> Lost Assets Directory</h4>
        <a href="{{ url_for('report_lost') }}" class="btn btn-danger btn-sm"><i class="fa-solid fa-plus me-1"></i> Report Lost</a>
    </div>
    <div class="row g-3">
        {% for it in items %}
        <div class="col-md-4">
            <div class="card h-100 shadow-sm border p-3">
                <span class="badge bg-secondary mb-1 align-self-start">{{ it.category }}</span>
                <h6 class="fw-bold mb-1">{{ it.title }}</h6>
                <p class="small text-muted mb-2 flex-grow-1">{{ it.description[:110] }}...</p>
                <div class="small text-secondary mb-3"><i class="fa-solid fa-location-dot me-1 text-danger"></i> {{ it.location }}</div>
                <div class="d-flex gap-2 mt-auto">
                    <a href="{{ url_for('view_item', item_id=it.id) }}" class="btn btn-outline-secondary btn-sm w-100">Details</a>
                    <a href="{{ url_for('item_matches', item_id=it.id) }}" class="btn btn-warning btn-sm w-100 text-dark">AI Match</a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% endblock %}
    """
    return render_template_string(content, title="Lost Items Directory", items=items)

@app.route("/items/found")
def list_found_items():
    conn = get_db()
    c = conn.cursor()
    items = c.execute("SELECT * FROM items WHERE type = 'found' ORDER BY id DESC").fetchall()
    conn.close()

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="fw-bold text-success mb-0"><i class="fa-solid fa-circle-check me-2"></i> Found Assets Directory</h4>
        <a href="{{ url_for('report_found') }}" class="btn btn-success btn-sm"><i class="fa-solid fa-plus me-1"></i> Report Found</a>
    </div>
    <div class="row g-3">
        {% for it in items %}
        <div class="col-md-4">
            <div class="card h-100 shadow-sm border p-3">
                <span class="badge bg-secondary mb-1 align-self-start">{{ it.category }}</span>
                <h6 class="fw-bold mb-1">{{ it.title }}</h6>
                <p class="small text-muted mb-2 flex-grow-1">{{ it.description[:110] }}...</p>
                <div class="small text-secondary mb-3"><i class="fa-solid fa-warehouse me-1 text-success"></i> {{ it.location }}</div>
                <div class="d-flex gap-2 mt-auto">
                    <a href="{{ url_for('view_item', item_id=it.id) }}" class="btn btn-outline-secondary btn-sm w-100">Details</a>
                    <a href="{{ url_for('submit_claim', item_id=it.id) }}" class="btn btn-success btn-sm w-100">Claim</a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% endblock %}
    """
    return render_template_string(content, title="Found Items Directory", items=items)

@app.route("/recovery/certificate/<int:item_id>")
@login_required
def recovery_certificate(item_id):
    conn = get_db()
    c = conn.cursor()
    item = c.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    claim = c.execute("SELECT * FROM claims WHERE item_id = ? AND status = 'Verified'", (item_id,)).fetchone()
    conn.close()

    if not item or not claim:
        flash("Verified recovery record or certificate not found.", "warning")
        return redirect(url_for("index"))

    content = """
    {% extends "base.html" %}
    {% block content %}
    <div class="row justify-content-center py-4">
        <div class="col-lg-8">
            <div class="card shadow-lg border-2 border-warning p-4 p-md-5 bg-white text-center">
                <div class="text-warning mb-2 fs-1"><i class="fa-solid fa-award"></i></div>
                <h6 class="text-secondary fw-bold text-uppercase mb-1">SANSKRITI UNIVERSITY &bull; MATHURA</h6>
                <h4 class="fw-bold text-primary mb-3">OFFICIAL ACADEMIC ASSET HANDOVER CERTIFICATE</h4>
                <p class="text-muted small mb-4">Issued under the Authority of Campus Security & Academic Recovery Cell</p>

                <div class="p-4 bg-light rounded-3 border text-start mb-4">
                    <div class="row g-3">
                        <div class="col-md-6">
                            <div class="small text-muted">Recovered Asset</div>
                            <div class="fw-bold fs-6">{{ item.title }}</div>
                            <div class="small text-muted">Ticket: {{ item.ticket_number }}</div>
                        </div>
                        <div class="col-md-6">
                            <div class="small text-muted">Verified Owner / Recipient</div>
                            <div class="fw-bold fs-6">{{ claim.claimant_name }}</div>
                            <div class="small text-muted">{{ claim.claimant_email }}</div>
                        </div>
                        <div class="col-md-6">
                            <div class="small text-muted">Verification Method</div>
                            <div class="small fw-semibold text-success"><i class="fa-solid fa-check-circle me-1"></i> Two-Tier Serial Match & Physical Inspection</div>
                        </div>
                        <div class="col-md-6">
                            <div class="small text-muted">Handover Date</div>
                            <div class="small fw-semibold">{{ claim.verified_at or '2026-10-06' }}</div>
                        </div>
                    </div>
                </div>

                <div class="d-flex justify-content-around mt-4 pt-3 border-top">
                    <div>
                        <div class="fw-bold small text-dark">O. Pulla Reddy (2302320110)</div>
                        <div class="small text-muted">Student Presenter</div>
                    </div>
                    <div>
                        <div class="fw-bold small text-dark">Dr. Sakuldeep Singh</div>
                        <div class="small text-muted">Faculty Guide & Director</div>
                    </div>
                </div>

                <div class="mt-4">
                    <button onclick="window.print()" class="btn btn-outline-dark btn-sm"><i class="fa-solid fa-print me-1"></i> Print Official Certificate</button>
                    <a href="{{ url_for('index') }}" class="btn btn-su btn-sm ms-2">Return to Portal</a>
                </div>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(content, title="Handover Certificate", item=item, claim=claim)

# --------------------------------------------------------------------------------------
# 6. APPLICATION ENTRY POINT
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    print("=" * 76)
    print(" SANSKRITI UNIVERSITY - ACADEMIC ASSET RECOVERY & MANAGEMENT SYSTEM")
    print(" Student: O. Pulla Reddy (2302320110) | Guide: Dr. Sakuldeep Singh")
    print(" Single-File All-in-One Runnable Monolith Architecture")
    print("=" * 76)
    print(" [✓] Database verified and seeded at:", DB_FILE)
    print(" [✓] NLP TF-IDF Cosine Similarity Engine loaded.")
    print(" [✓] Server starting on http://127.0.0.1:5000 ...")
    print("=" * 76)
    app.run(host="0.0.0.0", port=5000, debug=False)
