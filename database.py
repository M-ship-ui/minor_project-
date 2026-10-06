import sqlite3
import os
from flask import g

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'academic_assets.db')

def get_db():
    """Get or open database connection for the current Flask request context."""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    """Close the database connection if open."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_raw_connection():
    """Get standalone connection for scripts/background jobs outside request context."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def query_db(query, args=(), one=False, conn=None):
    """Execute query and fetch rows."""
    close_after = False
    if conn is None:
        try:
            conn = get_db()
        except RuntimeError:
            conn = get_raw_connection()
            close_after = True
    
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    if close_after:
        conn.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=(), conn=None):
    """Execute update/delete/insert and commit."""
    close_after = False
    if conn is None:
        try:
            conn = get_db()
        except RuntimeError:
            conn = get_raw_connection()
            close_after = True
            
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    last_id = cur.lastrowid
    cur.close()
    if close_after:
        conn.close()
    return last_id

def log_audit(user_id, user_name, action, target_type, target_id, details, conn=None):
    """Record an audit trail event."""
    try:
        execute_db(
            """INSERT INTO audit_logs (user_id, user_name, action, target_type, target_id, details)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, user_name or 'System/Anonymous', action, target_type, target_id, details),
            conn=conn
        )
    except Exception as e:
        print(f"Error logging audit: {e}")

def create_notification(user_id, title, message, notif_type='system', link=None, conn=None):
    """Create in-app user notification."""
    try:
        execute_db(
            """INSERT INTO notifications (user_id, title, message, type, link)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, title, message, notif_type, link),
            conn=conn
        )
    except Exception as e:
        print(f"Error creating notification: {e}")

def log_simulated_email(recipient_email, recipient_name, subject, body, conn=None):
    """Simulate dispatching a campus notification email."""
    try:
        execute_db(
            """INSERT INTO email_logs (recipient_email, recipient_name, subject, body)
               VALUES (?, ?, ?, ?)""",
            (recipient_email, recipient_name or recipient_email, subject, body),
            conn=conn
        )
    except Exception as e:
        print(f"Error logging email: {e}")

def init_db():
    """Create all database tables and essential indices."""
    conn = get_raw_connection()
    cursor = conn.cursor()
    
    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        department TEXT NOT NULL,
        id_number TEXT NOT NULL,
        phone TEXT,
        avatar TEXT DEFAULT 'default_avatar.png',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Items table (Lost and Found items)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_number TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL, -- 'lost' or 'found'
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        department TEXT NOT NULL,
        location TEXT NOT NULL,
        building_zone TEXT NOT NULL,
        date_event TEXT NOT NULL,
        time_event TEXT,
        image_path TEXT,
        user_id INTEGER,
        reporter_name TEXT,
        reporter_contact TEXT,
        is_anonymous INTEGER DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Lost', -- 'Lost', 'Found', 'Under Claim', 'Verified', 'Returned', 'Closed'
        serial_number_hint TEXT,
        identifying_marks TEXT,
        storage_location TEXT,
        escalated INTEGER DEFAULT 0,
        escalation_reason TEXT,
        escalated_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
    );
    """)

    # 3. Institutional assets table (University inventory)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS institutional_assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_tag TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        model_specs TEXT,
        serial_number TEXT,
        department TEXT NOT NULL,
        assigned_to TEXT,
        current_location TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Active', -- 'Active', 'Under Maintenance', 'Reported Lost', 'Decommissioned'
        registered_date TEXT,
        value_estimate REAL DEFAULT 0.0
    );
    """)

    # 4. Claims table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claim_number TEXT UNIQUE NOT NULL,
        item_id INTEGER NOT NULL,
        claimant_id INTEGER NOT NULL,
        proof_description TEXT NOT NULL,
        proof_serial_number TEXT,
        unique_identifiers TEXT,
        proof_image_path TEXT,
        status TEXT NOT NULL DEFAULT 'Under Claim', -- 'Under Claim', 'Verified', 'Rejected', 'Approved', 'Handed Over'
        admin_notes TEXT,
        verified_by INTEGER,
        verified_at TIMESTAMP,
        handover_officer TEXT,
        handover_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
        FOREIGN KEY (claimant_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (verified_by) REFERENCES users (id) ON DELETE SET NULL
    );
    """)

    # 5. AI Matches table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lost_item_id INTEGER NOT NULL,
        found_item_id INTEGER NOT NULL,
        text_similarity_score REAL NOT NULL,
        category_score REAL NOT NULL,
        location_score REAL NOT NULL,
        visual_score REAL DEFAULT 0.0,
        composite_score REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Suggested', -- 'Suggested', 'Confirmed', 'Dismissed', 'Resolved'
        match_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lost_item_id) REFERENCES items (id) ON DELETE CASCADE,
        FOREIGN KEY (found_item_id) REFERENCES items (id) ON DELETE CASCADE,
        UNIQUE(lost_item_id, found_item_id)
    );
    """)

    # 6. Audit logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_name TEXT,
        action TEXT NOT NULL,
        target_type TEXT NOT NULL,
        target_id INTEGER,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
    );
    """)

    # 7. Notifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT NOT NULL DEFAULT 'system',
        link TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 8. Email Logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_email TEXT NOT NULL,
        recipient_name TEXT,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 9. Recovery History table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recovery_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recovery_number TEXT UNIQUE NOT NULL,
        lost_item_id INTEGER,
        found_item_id INTEGER,
        claim_id INTEGER,
        item_title TEXT NOT NULL,
        category TEXT NOT NULL,
        owner_name TEXT NOT NULL,
        owner_email TEXT NOT NULL,
        finder_name TEXT,
        handover_officer TEXT NOT NULL,
        handover_desk TEXT NOT NULL,
        resolution_days INTEGER DEFAULT 1,
        remarks TEXT,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Indices for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_user_id ON items(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_item_id ON claims(item_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_claimant_id ON claims(claimant_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_matches_composite ON ai_matches(composite_score);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully at:", DB_PATH)

if __name__ == '__main__':
    init_db()
