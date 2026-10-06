from functools import wraps
from flask import session, redirect, url_for, flash, g, request
import database

def get_current_user():
    """Fetch current authenticated user object or None."""
    if 'user_id' not in session:
        return None
    user = database.query_db("SELECT * FROM users WHERE id = ?", (session['user_id'],), one=True)
    return user

def login_required(f):
    """Decorator to enforce authenticated session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in with your university account to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Decorator to enforce role permissions (e.g. admin, dept_head, staff)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for('login', next=request.url))
            
            user_role = session.get('role', 'student')
            if user_role not in allowed_roles and 'admin' not in allowed_roles and user_role != 'admin':
                flash("Access denied: You do not have permission to view this administrative resource.", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
