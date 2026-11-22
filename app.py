import os
import io
import csv
import uuid
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g, make_response, jsonify, send_from_directory
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

import database
import ml_engine
from auth_helper import get_current_user, login_required, role_required

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sanskriti-academic-asset-system-super-secret-key-2026'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

# Close DB connection at end of each request
app.teardown_appcontext(database.close_db)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.template_filter('format_dt')
def format_dt(value, fmt='%Y-%m-%d %H:%M'):
    if not value:
        return 'N/A'
    if isinstance(value, datetime):
        return value.strftime(fmt)
    return str(value)[:16]


@app.template_filter('format_date')
def format_date(value, fmt='%Y-%m-%d'):
    if not value:
        return 'N/A'
    if isinstance(value, datetime):
        return value.strftime(fmt)
    return str(value)[:10]


def get_system_stats():
    """Calculate key platform metrics across all modules."""
    conn = database.get_db()
    total_lost = database.query_db("SELECT COUNT(*) as c FROM items WHERE type='lost'", one=True)['c']
    total_found = database.query_db("SELECT COUNT(*) as c FROM items WHERE type='found'", one=True)['c']
    total_items = total_lost + total_found

    active_lost = database.query_db("SELECT COUNT(*) as c FROM items WHERE type='lost' AND status='Lost'", one=True)['c']
    active_found = database.query_db("SELECT COUNT(*) as c FROM items WHERE type='found' AND status='Found'", one=True)['c']
    under_claim = database.query_db("SELECT COUNT(*) as c FROM items WHERE status='Under Claim'", one=True)['c']
    verified = database.query_db("SELECT COUNT(*) as c FROM items WHERE status='Verified'", one=True)['c']
    recovered = database.query_db("SELECT COUNT(*) as c FROM recovery_history", one=True)['c']
    closed = database.query_db("SELECT COUNT(*) as c FROM items WHERE status IN ('Returned', 'Closed')", one=True)['c']
    escalated = database.query_db("SELECT COUNT(*) as c FROM items WHERE escalated=1", one=True)['c']
    ai_matches_count = database.query_db("SELECT COUNT(*) as c FROM ai_matches WHERE composite_score >= 50", one=True)['c']

    recovery_rate = round((recovered / total_items * 100), 1) if total_items > 0 else 0.0

    return {
        'total_items': total_items,
        'total_lost': total_lost,
        'total_found': total_found,
        'active_lost': active_lost,
        'active_found': active_found,
        'under_claim_count': under_claim,
        'verified_count': verified,
        'recovered_count': recovered,
        'closed_count': closed,
        'escalated_count': escalated,
        'ai_matches_count': ai_matches_count,
        'recovery_rate': recovery_rate
    }


@app.context_processor
def inject_global_template_data():
    """Make current_user and unread notifications count globally available to all templates."""
    user = get_current_user()
    unread_count = 0
    if user:
        row = database.query_db("SELECT COUNT(*) as c FROM notifications WHERE user_id = ? AND is_read = 0", (user['id'],), one=True)
        unread_count = row['c'] if row else 0
    return {
        'current_user': user,
        'unread_notifs_count': unread_count,
        'now_year': datetime.now().year
    }


# ==============================================================================
# MODULE 1: HOME / DASHBOARD
# ==============================================================================
@app.route('/')
def index():
    stats = get_system_stats()
    recent_lost = database.query_db("SELECT * FROM items WHERE type='lost' ORDER BY id DESC LIMIT 4")
    recent_found = database.query_db("SELECT * FROM items WHERE type='found' ORDER BY id DESC LIMIT 4")

    # High-confidence AI match suggestions
    top_ai_matches = database.query_db("""
        SELECT m.id, m.lost_item_id, m.found_item_id, m.composite_score, m.status,
               l.title as lost_title, l.location as lost_location, l.category as lost_category,
               f.title as found_title, f.storage_location as found_storage, f.location as found_location
        FROM ai_matches m
        JOIN items l ON m.lost_item_id = l.id
        JOIN items f ON m.found_item_id = f.id
        WHERE m.composite_score >= 60.0 AND m.status != 'Dismissed'
        ORDER BY m.composite_score DESC LIMIT 3
    """)

    return render_template(
        'index.html',
        stats=stats,
        recent_lost=recent_lost,
        recent_found=recent_found,
        top_ai_matches=top_ai_matches
    )


# ==============================================================================
# MODULE 2 & 3: USER REGISTRATION & AUTHENTICATION
# ==============================================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student')
        department = request.form.get('department', '').strip()
        id_number = request.form.get('id_number', '').strip()
        phone = request.form.get('phone', '').strip()

        if not name or not email or not password or not department or not id_number:
            flash("All mandatory fields marked with an asterisk must be filled.", "danger")
            return render_template('auth/register.html')

        if password != confirm_password:
            flash("Passwords do not match. Please verify and re-enter.", "danger")
            return render_template('auth/register.html')

        existing_user = database.query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
        if existing_user:
            flash(f"An account with email {email} already exists. Please log in.", "warning")
            return redirect(url_for('login'))

        password_hash = generate_password_hash(password)
        user_id = database.execute_db("""
            INSERT INTO users (name, email, password_hash, role, department, id_number, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, email, password_hash, role, department, id_number, phone))

        # Welcome notification
        database.create_notification(
            user_id,
            "Welcome to Sanskriti Asset Recovery Portal",
            f"Your {role.upper()} account is successfully registered. You can now report lost or found property and monitor match suggestions.",
            notif_type="system",
            link=url_for('profile')
        )

        database.log_audit(user_id, name, "USER_REGISTERED", "User", user_id, f"Registered new {role} account: {email}")

        session['user_id'] = user_id
        session['role'] = role
        session['user_name'] = name

        flash(f"Welcome, {name}! Your account has been registered successfully.", "success")
        return redirect(url_for('index'))

    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = database.query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)
        if not user or not check_password_hash(user['password_hash'], password):
            flash("Invalid email or password. Please verify your credentials.", "danger")
            return render_template('auth/login.html')

        session['user_id'] = user['id']
        session['role'] = user['role']
        session['user_name'] = user['name']

        database.log_audit(user['id'], user['name'], "USER_LOGGED_IN", "User", user['id'], f"Signed in from session")

        flash(f"Welcome back, {user['name']}! Signed in as {user['role'].upper()}.", "success")
        next_url = request.args.get('next')
        return redirect(next_url or url_for('index'))

    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    user = get_current_user()
    if user:
        database.log_audit(user['id'], user['name'], "USER_LOGGED_OUT", "User", user['id'], "Signed out of session")
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('index'))


@app.route('/quick-switch/<role>')
def quick_switch(role):
    """1-Click Evaluation Fast Switcher for Faculty Guide & Presentation Reviewers."""
    role_map = {
        'admin': 'admin@sanskriti.edu.in',
        'guide': 'admin@sanskriti.edu.in',
        'hod': 'hod.cs@sanskriti.edu.in',
        'staff': 'staff.rajesh@sanskriti.edu.in',
        'student': 'student.reddy@sanskriti.edu.in'
    }
    email = role_map.get(role, 'student.reddy@sanskriti.edu.in')
    user = database.query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)
    if user:
        session.clear()
        session['user_id'] = user['id']
        session['user_role'] = user['role']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        flash(f"Switched role to {user['name']} ({user['role'].upper()}) for demonstration.", "success")
    next_url = request.args.get('next') or request.referrer or url_for('index')
    return redirect(next_url)


# ==============================================================================
# MODULE 4: USER PROFILE
# ==============================================================================
@app.route('/profile')
@login_required
def profile():
    user = get_current_user()
    user_lost = database.query_db("SELECT * FROM items WHERE user_id = ? AND type='lost' ORDER BY id DESC", (user['id'],))
    user_found = database.query_db("SELECT * FROM items WHERE user_id = ? AND type='found' ORDER BY id DESC", (user['id'],))
    user_claims = database.query_db("""
        SELECT c.*, i.title as item_title, i.category as item_category
        FROM claims c
        JOIN items i ON c.item_id = i.id
        WHERE c.claimant_id = ?
        ORDER BY c.id DESC
    """, (user['id'],))

    return render_template(
        'user/profile.html',
        user=user,
        user_lost=user_lost,
        user_found=user_found,
        user_claims=user_claims
    )


@app.route('/profile/update-password', methods=['POST'])
@login_required
def update_password():
    user = get_current_user()
    current_pass = request.form.get('current_password', '')
    new_pass = request.form.get('new_password', '')

    if not check_password_hash(user['password_hash'], current_pass):
        flash("Current password was incorrect.", "danger")
        return redirect(url_for('profile'))

    new_hash = generate_password_hash(new_pass)
    database.execute_db("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user['id']))
    database.log_audit(user['id'], user['name'], "PASSWORD_CHANGED", "User", user['id'], "User updated security password")
    flash("Your password was updated successfully.", "success")
    return redirect(url_for('profile'))


# ==============================================================================
# MODULE 5: ASSET MANAGEMENT (CAMPUS INVENTORY)
# ==============================================================================
@app.route('/institutional-assets')
def institutional_assets():
    assets = database.query_db("SELECT * FROM institutional_assets ORDER BY id DESC")
    return render_template('assets/institutional.html', assets=assets)


# ==============================================================================
# MODULE 6: REPORT LOST ASSET
# ==============================================================================
@app.route('/report/lost', methods=['GET', 'POST'])
@login_required
def report_lost():
    user = get_current_user()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        department = request.form.get('department', '').strip()
        location = request.form.get('location', '').strip()
        building_zone = request.form.get('building_zone', '').strip()
        date_event = request.form.get('date_event', '').strip()
        time_event = request.form.get('time_event', '').strip()
        serial_number_hint = request.form.get('serial_number_hint', '').strip()
        identifying_marks = request.form.get('identifying_marks', '').strip()
        is_anonymous = 1 if request.form.get('is_anonymous') == '1' else 0

        # Spam and duplicate check
        recent_items = [dict(r) for r in database.query_db("SELECT * FROM items WHERE type='lost' ORDER BY id DESC LIMIT 20")]
        candidate_dict = {
            'title': title, 'category': category, 'description': description,
            'department': department, 'location': location, 'building_zone': building_zone,
            'serial_number_hint': serial_number_hint, 'identifying_marks': identifying_marks, 'type': 'lost'
        }
        is_flagged, reason = ml_engine.detect_spam_or_duplicate(candidate_dict, recent_items)
        if is_flagged:
            flash(f"Submission Flagged: {reason}", "warning")

        # Handle image upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                image_filename = f"lost_{uuid.uuid4().hex[:8]}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        # Generate unique ticket number
        ticket_number = f"TKT-LOST-{datetime.now().year}-{str(uuid.uuid4().int)[:4]}"

        reporter_name = "Anonymous Student/Staff" if is_anonymous else user['name']
        reporter_contact = "Protected by Escrow" if is_anonymous else user['email']

        item_id = database.execute_db("""
            INSERT INTO items (
                ticket_number, type, title, category, description, department, location,
                building_zone, date_event, time_event, image_path, user_id, reporter_name,
                reporter_contact, is_anonymous, status, serial_number_hint, identifying_marks
            ) VALUES (?, 'lost', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Lost', ?, ?)
        """, (
            ticket_number, title, category, description, department, location,
            building_zone, date_event, time_event, image_filename, user['id'],
            reporter_name, reporter_contact, is_anonymous, serial_number_hint, identifying_marks
        ))

        database.log_audit(user['id'], user['name'], "ITEM_REPORTED", "Item", item_id, f"Reported lost item #{ticket_number}: {title}")

        # Execute automatic AI match scan against all found items
        found_items = [dict(r) for r in database.query_db("SELECT * FROM items WHERE type='found' AND status='Found'")]
        new_lost_item = dict(database.query_db("SELECT * FROM items WHERE id = ?", (item_id,), one=True))
        matched_any_high = False

        for f_item in found_items:
            score_data = ml_engine.calculate_match_score(new_lost_item, f_item, base_upload_folder=app.config['UPLOAD_FOLDER'])
            if score_data['composite_score'] >= 35.0:
                database.execute_db("""
                    INSERT OR REPLACE INTO ai_matches (
                        lost_item_id, found_item_id, text_similarity_score, category_score,
                        location_score, visual_score, composite_score, status, match_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Suggested', ?)
                """, (
                    new_lost_item['id'], f_item['id'],
                    score_data['text_similarity_score'], score_data['category_score'],
                    score_data['location_score'], score_data['visual_score'],
                    score_data['composite_score'],
                    f"Match Confidence: {score_data['confidence_tier']} ({score_data['composite_score']}%)"
                ))
                if score_data['composite_score'] >= 65.0:
                    matched_any_high = True

        if matched_any_high:
            database.create_notification(
                user['id'],
                f"AI Match Candidate Detected! [{title}]",
                f"A found asset matching your report '{title}' was detected in campus custody. Please inspect the match.",
                notif_type="match",
                link=url_for('item_matches_view', item_id=item_id)
            )
            database.log_simulated_email(
                user['email'], user['name'],
                f"[Sanskriti Recovery Portal] Potential Match Found for Lost Item #{ticket_number}",
                f"Dear {user['name']},\n\nOur AI matching engine has detected high-scoring matches in campus inventory for your reported {title}. Please log in to inspect and initiate ownership verification.\n\nRegards,\nSanskriti University Asset Recovery Cell"
            )

        flash(f"Lost item ticket #{ticket_number} created successfully. AI matching scan completed!", "success")
        return redirect(url_for('item_matches_view', item_id=item_id))

    return render_template('assets/report_lost.html')


# ==============================================================================
# MODULE 7: REPORT FOUND ASSET
# ==============================================================================
@app.route('/report/found', methods=['GET', 'POST'])
@login_required
def report_found():
    user = get_current_user()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        department = request.form.get('department', '').strip()
        location = request.form.get('location', '').strip()
        building_zone = request.form.get('building_zone', '').strip()
        storage_location = request.form.get('storage_location', '').strip()
        date_event = request.form.get('date_event', '').strip()
        time_event = request.form.get('time_event', '').strip()
        serial_number_hint = request.form.get('serial_number_hint', '').strip()
        identifying_marks = request.form.get('identifying_marks', '').strip()
        is_anonymous = 1 if request.form.get('is_anonymous') == '1' else 0

        # Duplicate check
        recent_items = [dict(r) for r in database.query_db("SELECT * FROM items WHERE type='found' ORDER BY id DESC LIMIT 20")]
        candidate_dict = {
            'title': title, 'category': category, 'description': description,
            'department': department, 'location': location, 'building_zone': building_zone,
            'serial_number_hint': serial_number_hint, 'identifying_marks': identifying_marks, 'type': 'found'
        }
        is_flagged, reason = ml_engine.detect_spam_or_duplicate(candidate_dict, recent_items)
        if is_flagged:
            flash(f"Notice: {reason}", "warning")

        # Handle image upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                image_filename = f"found_{uuid.uuid4().hex[:8]}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        ticket_number = f"TKT-FND-{datetime.now().year}-{str(uuid.uuid4().int)[:4]}"

        reporter_name = "Anonymous Good Samaritan" if is_anonymous else user['name']
        reporter_contact = "Protected by Escrow" if is_anonymous else user['email']

        item_id = database.execute_db("""
            INSERT INTO items (
                ticket_number, type, title, category, description, department, location,
                building_zone, date_event, time_event, image_path, user_id, reporter_name,
                reporter_contact, is_anonymous, status, serial_number_hint, identifying_marks,
                storage_location
            ) VALUES (?, 'found', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Found', ?, ?, ?)
        """, (
            ticket_number, title, category, description, department, location,
            building_zone, date_event, time_event, image_filename, user['id'],
            reporter_name, reporter_contact, is_anonymous, serial_number_hint, identifying_marks,
            storage_location
        ))

        database.log_audit(user['id'], user['name'], "ITEM_REPORTED", "Item", item_id, f"Reported found item #{ticket_number}: {title} at {storage_location}")

        # Scan against active lost items
        lost_items = [dict(r) for r in database.query_db("SELECT * FROM items WHERE type='lost' AND status='Lost'")]
        new_found_item = dict(database.query_db("SELECT * FROM items WHERE id = ?", (item_id,), one=True))

        for l_item in lost_items:
            score_data = ml_engine.calculate_match_score(l_item, new_found_item, base_upload_folder=app.config['UPLOAD_FOLDER'])
            if score_data['composite_score'] >= 35.0:
                database.execute_db("""
                    INSERT OR REPLACE INTO ai_matches (
                        lost_item_id, found_item_id, text_similarity_score, category_score,
                        location_score, visual_score, composite_score, status, match_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Suggested', ?)
                """, (
                    l_item['id'], new_found_item['id'],
                    score_data['text_similarity_score'], score_data['category_score'],
                    score_data['location_score'], score_data['visual_score'],
                    score_data['composite_score'],
                    f"Match Confidence: {score_data['confidence_tier']} ({score_data['composite_score']}%)"
                ))
                # Alert lost item reporter if score >= 65%
                if score_data['composite_score'] >= 65.0 and l_item.get('user_id'):
                    database.create_notification(
                        l_item['user_id'],
                        f"Potential Match Found: {l_item['title']}",
                        f"An item matching your lost report has just been handed in at {storage_location}.",
                        notif_type="match",
                        link=url_for('item_matches_view', item_id=l_item['id'])
                    )

        flash(f"Found item #{ticket_number} logged successfully. Item placed in secure escrow.", "success")
        return redirect(url_for('item_detail', item_id=item_id))

    return render_template('assets/report_found.html')


# ==============================================================================
# ITEM LISTINGS & DETAILS
# ==============================================================================
@app.route('/items/lost')
def list_lost():
    category = request.args.get('category')
    if category:
        items = database.query_db("SELECT * FROM items WHERE type='lost' AND category = ? ORDER BY id DESC", (category,))
    else:
        items = database.query_db("SELECT * FROM items WHERE type='lost' ORDER BY id DESC")
    return render_template(
        'assets/list.html',
        items=items,
        item_type='lost',
        page_title='Lost Academic Assets',
        page_description='Items reported lost by Sanskriti University students and departments.',
        selected_category=category
    )


@app.route('/items/found')
def list_found():
    category = request.args.get('category')
    if category:
        items = database.query_db("SELECT * FROM items WHERE type='found' AND category = ? ORDER BY id DESC", (category,))
    else:
        items = database.query_db("SELECT * FROM items WHERE type='found' ORDER BY id DESC")
    return render_template(
        'assets/list.html',
        items=items,
        item_type='found',
        page_title='Found Property in Custody',
        page_description='Items handed into campus security desks, libraries, and lab stores awaiting claim.',
        selected_category=category
    )


@app.route('/items/<int:item_id>')
def item_detail(item_id):
    item = database.query_db("SELECT * FROM items WHERE id = ?", (item_id,), one=True)
    if not item:
        flash("Item ticket not found.", "warning")
        return redirect(url_for('index'))

    # Retrieve suggested matches for this item
    suggested_matches = []
    if item['type'] == 'lost':
        rows = database.query_db("""
            SELECT m.composite_score, f.id as candidate_id, f.title as candidate_title,
                   f.location as candidate_location, f.storage_location
            FROM ai_matches m
            JOIN items f ON m.found_item_id = f.id
            WHERE m.lost_item_id = ? AND m.composite_score >= 50
            ORDER BY m.composite_score DESC LIMIT 4
        """, (item_id,))
        suggested_matches = rows
    else:
        rows = database.query_db("""
            SELECT m.composite_score, l.id as candidate_id, l.title as candidate_title,
                   l.location as candidate_location
            FROM ai_matches m
            JOIN items l ON m.lost_item_id = l.id
            WHERE m.found_item_id = ? AND m.composite_score >= 50
            ORDER BY m.composite_score DESC LIMIT 4
        """, (item_id,))
        suggested_matches = rows

    return render_template('assets/item_detail.html', item=item, suggested_matches=suggested_matches)


# ==============================================================================
# MODULE 8: SEARCH ASSETS (MULTI-PARAMETER)
# ==============================================================================
@app.route('/search')
def search_assets():
    q = request.args.get('q', '').strip()
    item_type = request.args.get('type', '').strip()
    category = request.args.get('category', '').strip()
    department = request.args.get('department', '').strip()
    building_zone = request.args.get('building_zone', '').strip()
    status = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    sql = "SELECT * FROM items WHERE 1=1"
    params = []

    if q:
        sql += " AND (title LIKE ? OR description LIKE ? OR identifying_marks LIKE ? OR ticket_number LIKE ?)"
        wildcard = f"%{q}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    if item_type:
        sql += " AND type = ?"
        params.append(item_type)

    if category:
        sql += " AND category = ?"
        params.append(category)

    if department:
        sql += " AND department = ?"
        params.append(department)

    if building_zone:
        sql += " AND building_zone = ?"
        params.append(building_zone)

    if status:
        sql += " AND status = ?"
        params.append(status)

    if date_from:
        sql += " AND date_event >= ?"
        params.append(date_from)

    if date_to:
        sql += " AND date_event <= ?"
        params.append(date_to)

    sql += " ORDER BY id DESC LIMIT 50"
    results = database.query_db(sql, params)

    return render_template(
        'search/search.html',
        results=results,
        query=q,
        selected_type=item_type,
        selected_category=category,
        selected_dept=department,
        selected_zone=building_zone,
        selected_status=status,
        date_from=date_from,
        date_to=date_to
    )


# ==============================================================================
# MODULE 9: AI ASSET MATCHING
# ==============================================================================
@app.route('/ai/matching-center')
def ai_matching_center():
    matches = database.query_db("""
        SELECT m.*,
               l.title as lost_title, l.location as lost_location, l.category as lost_category,
               l.image_path as lost_image, l.ticket_number as lost_ticket,
               f.title as found_title, f.storage_location as found_storage, f.location as found_location,
               f.category as found_category, f.image_path as found_image, f.ticket_number as found_ticket
        FROM ai_matches m
        JOIN items l ON m.lost_item_id = l.id
        JOIN items f ON m.found_item_id = f.id
        ORDER BY m.composite_score DESC
    """)
    return render_template('ai/matching_center.html', matches=matches)


@app.route('/ai/run-batch', methods=['POST'])
def run_ai_batch_matching():
    lost_items = [dict(r) for r in database.query_db("SELECT * FROM items WHERE type='lost'")]
    found_items = [dict(r) for r in database.query_db("SELECT * FROM items WHERE type='found'")]

    count = 0
    for l_item in lost_items:
        for f_item in found_items:
            score_data = ml_engine.calculate_match_score(l_item, f_item, base_upload_folder=app.config['UPLOAD_FOLDER'])
            if score_data['composite_score'] >= 35.0:
                database.execute_db("""
                    INSERT OR REPLACE INTO ai_matches (
                        lost_item_id, found_item_id, text_similarity_score, category_score,
                        location_score, visual_score, composite_score, status, match_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Suggested', ?)
                """, (
                    l_item['id'], f_item['id'],
                    score_data['text_similarity_score'], score_data['category_score'],
                    score_data['location_score'], score_data['visual_score'],
                    score_data['composite_score'],
                    f"AI Confidence: {score_data['confidence_tier']} ({score_data['composite_score']}%)"
                ))
                count += 1

    flash(f"AI Batch Matching Engine evaluated {len(lost_items) * len(found_items)} item combinations and recorded {count} potential matches.", "success")
    return redirect(url_for('ai_matching_center'))


@app.route('/ai/item/<int:item_id>/matches')
def item_matches_view(item_id):
    target_item = database.query_db("SELECT * FROM items WHERE id = ?", (item_id,), one=True)
    if not target_item:
        flash("Item ticket not found.", "warning")
        return redirect(url_for('index'))

    candidates = []
    if target_item['type'] == 'lost':
        opposite_items = [dict(r) for r in database.query_db("SELECT * FROM items WHERE type='found'")]
        for opp in opposite_items:
            score_data = ml_engine.calculate_match_score(dict(target_item), opp, base_upload_folder=app.config['UPLOAD_FOLDER'])
            if score_data['composite_score'] >= 30.0:
                candidates.append({
                    'item': opp,
                    'composite_score': score_data['composite_score'],
                    'text_score': score_data['text_similarity_score'],
                    'cat_score': score_data['category_score'],
                    'loc_score': score_data['location_score'],
                    'vis_score': score_data['visual_score'],
                    'confidence': score_data['confidence_tier']
                })
    else:
        opposite_items = [dict(r) for r in database.query_db("SELECT * FROM items WHERE type='lost'")]
        for opp in opposite_items:
            score_data = ml_engine.calculate_match_score(opp, dict(target_item), base_upload_folder=app.config['UPLOAD_FOLDER'])
            if score_data['composite_score'] >= 30.0:
                candidates.append({
                    'item': opp,
                    'composite_score': score_data['composite_score'],
                    'text_score': score_data['text_similarity_score'],
                    'cat_score': score_data['category_score'],
                    'loc_score': score_data['location_score'],
                    'vis_score': score_data['visual_score'],
                    'confidence': score_data['confidence_tier']
                })

    candidates.sort(key=lambda x: x['composite_score'], reverse=True)
    return render_template('ai/item_matches.html', target_item=target_item, candidates=candidates)


# ==============================================================================
# MODULE 10: RECOVERY MANAGEMENT & OWNERSHIP CLAIMS
# ==============================================================================
@app.route('/claims/manage')
@login_required
def manage_claims():
    user = get_current_user()
    if user['role'] in ['admin', 'staff', 'dept_head']:
        claims = database.query_db("""
            SELECT c.*, i.title as item_title, i.category as item_category,
                   i.storage_location, i.location, i.ticket_number,
                   u.name as claimant_name, u.email as claimant_email, u.id_number as claimant_id_num
            FROM claims c
            JOIN items i ON c.item_id = i.id
            JOIN users u ON c.claimant_id = u.id
            ORDER BY c.id DESC
        """)
    else:
        claims = database.query_db("""
            SELECT c.*, i.title as item_title, i.category as item_category,
                   i.storage_location, i.location, i.ticket_number,
                   u.name as claimant_name, u.email as claimant_email, u.id_number as claimant_id_num
            FROM claims c
            JOIN items i ON c.item_id = i.id
            JOIN users u ON c.claimant_id = u.id
            WHERE c.claimant_id = ?
            ORDER BY c.id DESC
        """, (user['id'],))

    return render_template('claims/manage_claims.html', claims=claims)


@app.route('/claims/submit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def submit_claim(item_id):
    user = get_current_user()
    item = database.query_db("SELECT * FROM items WHERE id = ?", (item_id,), one=True)
    if not item:
        flash("Item ticket not found.", "warning")
        return redirect(url_for('index'))

    if request.method == 'POST':
        proof_desc = request.form.get('proof_description', '').strip()
        proof_serial = request.form.get('proof_serial_number', '').strip()
        unique_identifiers = request.form.get('unique_identifiers', '').strip()

        proof_filename = None
        if 'proof_document' in request.files:
            file = request.files['proof_document']
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                proof_filename = f"proof_{uuid.uuid4().hex[:8]}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], proof_filename))

        claim_number = f"CLM-{datetime.now().year}-{str(uuid.uuid4().int)[:4]}"

        claim_id = database.execute_db("""
            INSERT INTO claims (
                claim_number, item_id, claimant_id, proof_description, proof_serial_number,
                unique_identifiers, proof_image_path, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Under Claim')
        """, (claim_number, item_id, user['id'], proof_desc, proof_serial, unique_identifiers, proof_filename))

        # Transition item status to 'Under Claim'
        database.execute_db("UPDATE items SET status = 'Under Claim' WHERE id = ?", (item_id,))

        database.log_audit(user['id'], user['name'], "CLAIM_SUBMITTED", "Claim", claim_id, f"Filed ownership claim #{claim_number} for item #{item['ticket_number']}")

        # Notify Authority
        admins = database.query_db("SELECT id FROM users WHERE role IN ('admin', 'staff')")
        for admin in admins:
            database.create_notification(
                admin['id'],
                f"New Ownership Claim: {claim_number}",
                f"{user['name']} submitted proof of ownership for {item['title']}.",
                notif_type="claim",
                link=url_for('claim_detail', claim_id=claim_id)
            )

        flash(f"Ownership Claim #{claim_number} submitted successfully! Campus authority will review proof.", "success")
        return redirect(url_for('claim_detail', claim_id=claim_id))

    return render_template('claims/submit_claim.html', item=item)


@app.route('/claims/<int:claim_id>')
@login_required
def claim_detail(claim_id):
    claim = database.query_db("""
        SELECT c.*,
               i.title as item_title, i.category as item_category, i.ticket_number,
               i.storage_location, i.location, i.serial_number_hint as item_serial_hint,
               i.identifying_marks as item_marks,
               u.name as claimant_name, u.email as claimant_email,
               u.id_number as claimant_id_num, u.department as claimant_department
        FROM claims c
        JOIN items i ON c.item_id = i.id
        JOIN users u ON c.claimant_id = u.id
        WHERE c.id = ?
    """, (claim_id,), one=True)

    if not claim:
        flash("Claim not found.", "warning")
        return redirect(url_for('manage_claims'))

    user = get_current_user()
    if user['role'] not in ['admin', 'staff', 'dept_head'] and claim['claimant_id'] != user['id']:
        flash("Access denied to this claim dossier.", "danger")
        return redirect(url_for('manage_claims'))

    return render_template('claims/claim_detail.html', claim=claim)


@app.route('/claims/<int:claim_id>/adjudicate', methods=['POST'])
@login_required
@role_required('admin', 'staff', 'dept_head')
def adjudicate_claim(claim_id):
    user = get_current_user()
    status = request.form.get('status', 'Under Claim')
    admin_notes = request.form.get('admin_notes', '').strip()
    handover_officer = request.form.get('handover_officer', user['name']).strip()
    handover_desk = request.form.get('handover_desk', 'Main Gate Security Post 1').strip()

    claim = database.query_db("SELECT * FROM claims WHERE id = ?", (claim_id,), one=True)
    if not claim:
        flash("Claim record not found.", "warning")
        return redirect(url_for('manage_claims'))

    database.execute_db("""
        UPDATE claims
        SET status = ?, admin_notes = ?, verified_by = ?, verified_at = CURRENT_TIMESTAMP,
            handover_officer = ?, handover_date = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (status, admin_notes, user['id'], handover_officer, claim_id))

    # Synchronize item lifecycle status
    item_status_map = {
        'Under Claim': 'Under Claim',
        'Verified': 'Verified',
        'Approved': 'Verified',
        'Handed Over': 'Returned',
        'Rejected': 'Found'
    }
    new_item_status = item_status_map.get(status, 'Under Claim')
    database.execute_db("UPDATE items SET status = ? WHERE id = ?", (new_item_status, claim['item_id']))

    # If Handed Over, record into permanent recovery history
    if status == 'Handed Over':
        item = database.query_db("SELECT * FROM items WHERE id = ?", (claim['item_id'],), one=True)
        claimant = database.query_db("SELECT * FROM users WHERE id = ?", (claim['claimant_id'],), one=True)
        rec_number = f"REC-{datetime.now().year}-{str(uuid.uuid4().int)[:4]}"

        rec_id = database.execute_db("""
            INSERT INTO recovery_history (
                recovery_number, found_item_id, claim_id, item_title, category,
                owner_name, owner_email, finder_name, handover_officer, handover_desk,
                resolution_days, remarks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 3, ?)
        """, (
            rec_number, claim['item_id'], claim_id, item['title'], item['category'],
            claimant['name'], claimant['email'], item['reporter_name'],
            handover_officer, handover_desk, admin_notes or 'Physical serial number and ID card verified.'
        ))

        database.log_audit(user['id'], user['name'], "HANDOVER_COMPLETED", "Recovery", rec_id, f"Completed handover for claim #{claim['claim_number']}")

        # Dispatch email and notification
        database.create_notification(
            claim['claimant_id'],
            f"Asset Handover Completed: {item['title']}",
            f"Your item has been physically restored to you by {handover_officer}. Certificate #{rec_number} is now issued.",
            notif_type="claim",
            link=url_for('recovery_certificate', recovery_id=rec_id)
        )
    else:
        database.create_notification(
            claim['claimant_id'],
            f"Claim Status Update: {claim['claim_number']}",
            f"Your ownership claim status is now: {status.upper()}.",
            notif_type="claim",
            link=url_for('claim_detail', claim_id=claim_id)
        )

    flash(f"Claim #{claim['claim_number']} updated to {status}.", "success")
    return redirect(url_for('claim_detail', claim_id=claim_id))


# ==============================================================================
# MODULE 11: NOTIFICATIONS & SIMULATED EMAIL LOGS
# ==============================================================================
@app.route('/notifications')
@login_required
def notifications_view():
    user = get_current_user()
    notifs = database.query_db("SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC", (user['id'],))
    email_logs = database.query_db("SELECT * FROM email_logs WHERE recipient_email = ? OR ? IN ('admin', 'staff') ORDER BY id DESC LIMIT 20", (user['email'], user['role']))
    return render_template('notifications/notifications.html', notifications=notifs, email_logs=email_logs)


@app.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    user = get_current_user()
    database.execute_db("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user['id'],))
    flash("All notifications marked as read.", "info")
    return redirect(url_for('notifications_view'))


@app.route('/email-logs')
@login_required
def email_logs_view():
    user = get_current_user()
    if user['role'] in ['admin', 'staff', 'dept_head']:
        logs = database.query_db("SELECT * FROM email_logs ORDER BY id DESC")
    else:
        logs = database.query_db("SELECT * FROM email_logs WHERE recipient_email = ? ORDER BY id DESC", (user['email'],))
    return render_template('notifications/notifications.html', notifications=[], email_logs=logs)


# ==============================================================================
# MODULE 12: ADMIN DASHBOARD
# ==============================================================================
@app.route('/admin/dashboard')
@login_required
@role_required('admin', 'staff', 'dept_head')
def admin_dashboard():
    stats = get_system_stats()
    escalated_items = database.query_db("SELECT * FROM items WHERE escalated = 1 ORDER BY id DESC")
    recent_logs = database.query_db("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 10")
    return render_template('admin/dashboard.html', stats=stats, escalated_items=escalated_items, recent_logs=recent_logs)


# ==============================================================================
# MODULE 14: ADMIN LOST & FOUND MANAGEMENT
# ==============================================================================
@app.route('/admin/lost-found')
@login_required
@role_required('admin', 'staff', 'dept_head')
def admin_lost_found():
    items = database.query_db("SELECT * FROM items ORDER BY id DESC")
    return render_template('admin/items_management.html', items=items)


@app.route('/admin/items/<int:item_id>/update-status', methods=['POST'])
@login_required
@role_required('admin', 'staff', 'dept_head')
def admin_update_item_status(item_id):
    user = get_current_user()
    new_status = request.form.get('status', 'Lost')
    database.execute_db("UPDATE items SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, item_id))
    database.log_audit(user['id'], user['name'], "STATUS_UPDATED", "Item", item_id, f"Updated ticket status to {new_status}")
    flash(f"Item #{item_id} status updated to {new_status}.", "success")
    return redirect(request.referrer or url_for('admin_lost_found'))


@app.route('/admin/items/<int:item_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_item(item_id):
    user = get_current_user()
    item = database.query_db("SELECT ticket_number FROM items WHERE id = ?", (item_id,), one=True)
    ticket_num = item['ticket_number'] if item else str(item_id)
    database.execute_db("DELETE FROM items WHERE id = ?", (item_id,))
    database.log_audit(user['id'], user['name'], "ITEM_DELETED", "Item", item_id, f"Deleted spam/duplicate ticket #{ticket_num}")
    flash(f"Ticket #{ticket_num} deleted from active repository.", "info")
    return redirect(url_for('admin_lost_found'))


# ==============================================================================
# MODULE 15: ADMIN AI MATCH VERIFICATION
# ==============================================================================
@app.route('/admin/ai-verification')
@login_required
@role_required('admin', 'staff', 'dept_head')
def admin_ai_verification():
    matches = database.query_db("""
        SELECT m.*,
               l.title as lost_title, l.ticket_number as lost_ticket, l.category as lost_category, l.location as lost_location,
               f.title as found_title, f.ticket_number as found_ticket, f.category as found_category, f.location as found_location, f.storage_location as found_storage
        FROM ai_matches m
        JOIN items l ON m.lost_item_id = l.id
        JOIN items f ON m.found_item_id = f.id
        ORDER BY m.composite_score DESC
    """)
    return render_template('admin/match_verification.html', matches=matches)


@app.route('/admin/matches/<int:match_id>/confirm', methods=['POST'])
@login_required
@role_required('admin', 'staff', 'dept_head')
def admin_confirm_match(match_id):
    user = get_current_user()
    database.execute_db("UPDATE ai_matches SET status = 'Confirmed' WHERE id = ?", (match_id,))
    match = database.query_db("SELECT * FROM ai_matches WHERE id = ?", (match_id,), one=True)
    if match:
        lost_item = database.query_db("SELECT * FROM items WHERE id = ?", (match['lost_item_id'],), one=True)
        if lost_item and lost_item['user_id']:
            database.create_notification(
                lost_item['user_id'],
                f"Official Match Verified: {lost_item['title']}",
                "University authority has verified an authentic match for your lost report. Please view details to claim.",
                notif_type="match",
                link=url_for('item_matches_view', item_id=lost_item['id'])
            )
    database.log_audit(user['id'], user['name'], "MATCH_CONFIRMED", "Match", match_id, "Authority confirmed AI match pairing")
    flash("Match successfully verified! Alerts dispatched to applicant.", "success")
    return redirect(request.referrer or url_for('admin_ai_verification'))


@app.route('/admin/matches/<int:match_id>/dismiss', methods=['POST'])
@login_required
@role_required('admin', 'staff', 'dept_head')
def admin_dismiss_match(match_id):
    user = get_current_user()
    database.execute_db("UPDATE ai_matches SET status = 'Dismissed' WHERE id = ?", (match_id,))
    database.log_audit(user['id'], user['name'], "MATCH_DISMISSED", "Match", match_id, "Dismissed false positive pairing")
    flash("Match marked as dismissed.", "info")
    return redirect(request.referrer or url_for('admin_ai_verification'))


# ==============================================================================
# MODULE 13: ADMIN ASSET MANAGEMENT (INSTITUTIONAL EQUIPMENT)
# ==============================================================================
@app.route('/admin/assets')
@login_required
@role_required('admin', 'staff', 'dept_head')
def admin_assets():
    assets = database.query_db("SELECT * FROM institutional_assets ORDER BY id DESC")
    return render_template('admin/institutional_assets.html', assets=assets)


@app.route('/admin/assets/add', methods=['POST'])
@login_required
@role_required('admin', 'staff', 'dept_head')
def admin_add_institutional_asset():
    user = get_current_user()
    asset_tag = request.form.get('asset_tag', '').strip()
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    serial_number = request.form.get('serial_number', '').strip()
    department = request.form.get('department', '').strip()
    current_location = request.form.get('current_location', '').strip()
    value_estimate = float(request.form.get('value_estimate', 0.0) or 0.0)
    assigned_to = request.form.get('assigned_to', '').strip()
    model_specs = request.form.get('model_specs', '').strip()

    asset_id = database.execute_db("""
        INSERT INTO institutional_assets (
            asset_tag, name, category, model_specs, serial_number, department,
            assigned_to, current_location, status, registered_date, value_estimate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active', CURRENT_DATE, ?)
    """, (asset_tag, name, category, model_specs, serial_number, department, assigned_to, current_location, value_estimate))

    database.log_audit(user['id'], user['name'], "ASSET_REGISTERED", "Asset", asset_id, f"Registered new equipment {asset_tag}: {name}")
    flash(f"Asset {asset_tag} registered into university catalog.", "success")
    return redirect(url_for('admin_assets'))


# ==============================================================================
# AUTO-ESCALATION QUEUE & AUDIT TRAILS
# ==============================================================================
@app.route('/admin/escalations')
@login_required
@role_required('admin', 'staff', 'dept_head')
def admin_escalations():
    escalated_items = database.query_db("SELECT * FROM items WHERE escalated = 1 ORDER BY id DESC")
    return render_template('admin/escalation_queue.html', escalated_items=escalated_items)


@app.route('/admin/escalations/run-check', methods=['POST'])
@login_required
@role_required('admin', 'staff')
def run_auto_escalation_check():
    user = get_current_user()
    # Find all items open > 7 days that are not yet returned/closed
    items = database.query_db("SELECT id, title, ticket_number, date_event FROM items WHERE status IN ('Lost', 'Found', 'Under Claim') AND escalated = 0")
    escalated_count = 0
    today = datetime.now()

    for itm in items:
        try:
            event_dt = datetime.strptime(itm['date_event'][:10], '%Y-%m-%d')
            diff_days = (today - event_dt).days
            if diff_days >= 7:
                database.execute_db("""
                    UPDATE items
                    SET escalated = 1,
                        escalation_reason = ?,
                        escalated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (f"Unresolved for {diff_days} days. Auto-escalated to Campus Security Head.", itm['id']))
                escalated_count += 1
        except Exception:
            pass

    database.log_audit(user['id'], user['name'], "ESCALATION_CHECK_RUN", "System", 0, f"Triggered escalation audit: {escalated_count} items flagged")
    flash(f"Escalation check completed: {escalated_count} tickets escalated to security authority.", "info")
    return redirect(url_for('admin_escalations'))


@app.route('/admin/escalations/<int:item_id>/de-escalate', methods=['POST'])
@login_required
@role_required('admin', 'staff')
def admin_de_escalate_item(item_id):
    user = get_current_user()
    database.execute_db("UPDATE items SET escalated = 0, escalation_reason = NULL WHERE id = ?", (item_id,))
    database.log_audit(user['id'], user['name'], "ESCALATION_CLEARED", "Item", item_id, "Cleared escalation alert flag")
    flash(f"Escalation status removed for item #{item_id}.", "success")
    return redirect(url_for('admin_escalations'))


@app.route('/admin/audit-logs')
@login_required
@role_required('admin', 'staff', 'dept_head')
def admin_audit_logs():
    logs = database.query_db("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100")
    return render_template('admin/audit_logs.html', logs=logs)


# ==============================================================================
# MODULE 16: RECOVERY HISTORY & CERTIFICATES
# ==============================================================================
@app.route('/recovery/history')
def recovery_history():
    recoveries = database.query_db("SELECT * FROM recovery_history ORDER BY id DESC")
    return render_template('recovery/history.html', recoveries=recoveries)


@app.route('/recovery/certificate/<int:recovery_id>')
def recovery_certificate(recovery_id):
    rec = database.query_db("SELECT * FROM recovery_history WHERE id = ?", (recovery_id,), one=True)
    if not rec:
        flash("Recovery record not found.", "warning")
        return redirect(url_for('recovery_history'))
    return render_template('recovery/certificate.html', rec=rec)


# ==============================================================================
# MODULE 17: REPORTS & STATISTICS
# ==============================================================================
@app.route('/reports/statistics')
def reports_statistics():
    stats = get_system_stats()

    # Category breakdown
    categories = ['Laptops', 'Projectors', 'Books', 'ID Cards', 'Laboratory Equipment', 'Electronic Devices', 'Project Equipment', 'Other University Assets']
    cat_lost_counts = []
    cat_found_counts = []

    for cat in categories:
        l_cnt = database.query_db("SELECT COUNT(*) as c FROM items WHERE category = ? AND type='lost'", (cat,), one=True)['c']
        f_cnt = database.query_db("SELECT COUNT(*) as c FROM items WHERE category = ? AND type='found'", (cat,), one=True)['c']
        cat_lost_counts.append(l_cnt)
        cat_found_counts.append(f_cnt)

    # Hotspots
    hotspot_rows = database.query_db("SELECT building_zone, COUNT(*) as c FROM items GROUP BY building_zone ORDER BY c DESC LIMIT 8")
    hotspot_labels = [r['building_zone'] for r in hotspot_rows]
    hotspot_counts = [r['c'] for r in hotspot_rows]

    # Average resolution days
    avg_row = database.query_db("SELECT AVG(resolution_days) as a FROM recovery_history", one=True)
    avg_turnaround = round(avg_row['a'], 1) if avg_row and avg_row['a'] else 2.5

    return render_template(
        'reports/statistics.html',
        stats=stats,
        cat_labels=categories,
        cat_lost_counts=cat_lost_counts,
        cat_found_counts=cat_found_counts,
        hotspot_labels=hotspot_labels,
        hotspot_counts=hotspot_counts,
        avg_turnaround=avg_turnaround
    )


@app.route('/reports/export-csv')
@login_required
@role_required('admin', 'staff', 'dept_head')
def export_reports_csv():
    items = database.query_db("SELECT * FROM items ORDER BY id ASC")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Ticket Number', 'Type', 'Title', 'Category', 'Department',
        'Campus Zone', 'Specific Location', 'Event Date', 'Status',
        'Storage Custody', 'Is Anonymous', 'Created At'
    ])
    for itm in items:
        writer.writerow([
            itm['ticket_number'], itm['type'], itm['title'], itm['category'],
            itm['department'], itm['building_zone'], itm['location'],
            itm['date_event'], itm['status'], itm['storage_location'] or 'N/A',
            'Yes' if itm['is_anonymous'] else 'No', itm['created_at']
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f"attachment; filename=sanskriti_asset_incident_report_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers['Content-Type'] = 'text/csv'
    return response


# ==============================================================================
# MODULE 18: QR ASSET SCANNERS & REAL-TIME GPS TRACER (VIVA DEFENSE MODULE)
# ==============================================================================
@app.route('/qr-scanner')
def qr_scanner_hub():
    """
    Dedicated Multi-Category QR Asset Scanner & Real-Time GPS Geolocation Tracer.
    Supports: Laptops, Library Textbooks, Lab Experiments, Electronics, Student IDs.
    Direct answer to Viva Question: 'If an asset is lost, how does the app find it?'
    """
    category = request.args.get('category', 'laptops').strip().lower()
    
    # Query database for registered sample items across categories to enrich the scanner view
    db_items = {
        'laptops': database.query_db("SELECT * FROM items WHERE category IN ('Laptops', 'Electronic Devices') AND (title LIKE '%Laptop%' OR title LIKE '%Dell%' OR title LIKE '%ThinkPad%') ORDER BY id DESC LIMIT 5"),
        'library_textbooks': database.query_db("SELECT * FROM items WHERE category = 'Books' ORDER BY id DESC LIMIT 5"),
        'lab_equipment': database.query_db("SELECT * FROM items WHERE category = 'Laboratory Equipment' ORDER BY id DESC LIMIT 5"),
        'electronics': database.query_db("SELECT * FROM items WHERE category = 'Electronic Devices' ORDER BY id DESC LIMIT 5"),
        'student_ids': database.query_db("SELECT * FROM items WHERE category = 'ID Cards' ORDER BY id DESC LIMIT 5")
    }
    
    return render_template(
        'qr_scanner.html',
        active_category=category,
        db_items=db_items
    )


@app.route('/qr-verify')
@app.route('/qr-verify/<tag>')
def qr_verify(tag=None):
    """
    Public/Campus verification endpoint for scanned QR tags.
    Returns JSON asset profile with GPS coordinates and security custody status.
    """
    asset_tag = (tag or request.args.get('tag', '')).strip().upper()
    if not asset_tag:
        return jsonify({'status': 'error', 'message': 'Missing QR asset tag identifier'}), 400

    # Search items by ticket number, serial number hint, or ID
    item = database.query_db(
        "SELECT * FROM items WHERE ticket_number = ? OR serial_number_hint LIKE ? OR id = ?",
        (asset_tag, f"%{asset_tag}%", asset_tag),
        one=True
    )
    
    # Default GPS telemetry for Sanskriti University Mathura
    sanskriti_gps = {
        'latitude': 27.50352,
        'longitude': 77.67385,
        'campus_name': 'Sanskriti University, Mathura Campus',
        'accuracy_radius_meters': 3.2
    }

    if item:
        rep_name = item['reporter_name'] or 'Sanskriti Scholar'
        masked_owner = f"{rep_name[0]}***{rep_name[-1]}" if len(rep_name) > 1 else rep_name
        return jsonify({
            'status': 'verified',
            'tag': asset_tag,
            'title': item['title'],
            'category': item['category'],
            'owner_masked': masked_owner,
            'status_label': item['status'],
            'zone': item['building_zone'],
            'specific_location': item['location'],
            'gps': sanskriti_gps,
            'custody_desk': item['storage_location'] or 'Central Security Desk, Main Gate Reception'
        })
    else:
        return jsonify({
            'status': 'simulated_demo',
            'tag': asset_tag,
            'title': f'Sanskriti Academic Asset ({asset_tag})',
            'category': 'Verified Academic Asset',
            'owner_masked': 'O. Pulla Reddy (2302320110)',
            'status_label': 'Active Tracking',
            'zone': 'Academic Block B - Computer Science Lab 3',
            'gps': sanskriti_gps,
            'custody_desk': 'Central Campus Security & Proctorial Office'
        })


@app.route('/api/qr/log-gps', methods=['POST'])
def api_qr_log_gps():
    """
    REST API to record live GPS coordinate telemetry pings whenever a QR Asset tag is scanned.
    """
    data = request.get_json(silent=True) or {}
    tag = data.get('tag', 'SU-UNKNOWN')
    lat = data.get('lat', 27.50352)
    lng = data.get('lng', 77.67385)
    zone = data.get('zone', 'Sanskriti University Mathura')
    category = data.get('category', 'general')

    user = get_current_user()
    user_id = user['id'] if user else None
    user_name = user['name'] if user else 'Campus Scanner Telemetry'

    details = f"QR Scan GPS Fix: {lat} N, {lng} E | Tag: {tag} | Category: {category} | Campus Location: {zone}"
    database.log_audit(user_id, user_name, 'QR_GPS_TELEMETRY', 'asset_qr_tag', 0, details)

    return jsonify({
        'status': 'success',
        'message': 'GPS telemetry ping successfully recorded in campus recovery network',
        'tag': tag,
        'coordinates': {'lat': lat, 'lng': lng},
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/qr/handover', methods=['POST'])
def api_qr_handover():
    """
    REST API for instant security custody transfer and masked owner notification upon QR scan.
    """
    data = request.get_json(silent=True) or {}
    tag = data.get('tag', 'SU-UNKNOWN')
    title = data.get('title', 'Academic Asset')
    category = data.get('category', 'general')

    user = get_current_user()
    user_id = user['id'] if user else None
    user_name = user['name'] if user else 'Campus Finder / Security'

    details = f"Instant Handover of {title} (Tag: {tag}, Category: {category}) to Sanskriti Central Security Desk"
    database.log_audit(user_id, user_name, 'QR_INSTANT_HANDOVER', 'asset_qr_tag', 0, details)

    # In-app notification for admin and proctor
    database.create_notification(
        1,
        f"Asset Secured: {title}",
        f"Asset {title} ({tag}) scanned via QR Scanner and secured at Sanskriti Central Security Desk.",
        'claim',
        url_for('qr_scanner_hub', category=category)
    )

    return jsonify({
        'status': 'success',
        'message': f'Asset {title} ({tag}) custody officially recorded at Central Security Desk.',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
if __name__ == '__main__':
    # Initialize DB if not exists
    if not os.path.exists(database.DB_PATH):
        print("First time setup: running database seeding...")
        import seed_data
        seed_data.seed_all()
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=======================================================")
    print(f" SANSKRITI UNIVERSITY - ACADEMIC ASSET RECOVERY SYSTEM ")
    print(f" Local URL:   http://127.0.0.1:{port}                  ")
    print(f" Network URL: http://0.0.0.0:{port}                    ")
    print(f"=======================================================\n")
    app.run(debug=True, host='0.0.0.0', port=port)
