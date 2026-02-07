from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import get_db
import mysql.connector

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Registration
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        cpassword = request.form['cpassword']

        if cpassword != password:
            error = "Passwords do not match"
            return render_template('register.html', error=error)
        
        if len(password) < 6:
            error = "Password must be at least 6 characters long"
            return render_template('register.html', error=error)

        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO user (user_id, password) VALUES (%s, %s)",
                (user_id, password)
            )
            db.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('auth.login'))
        
        except mysql.connector.IntegrityError:
            error = "User ID already exists"
            
        finally:
            cursor.close()
            db.close()

    return render_template('register.html', error=error)


# Login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM user WHERE user_id=%s AND password=%s",
            (user_id, password)
        )
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if not user:
            error = "Invalid user ID or password"
            return render_template('login.html', error=error)
        
        # CREATE SESSION
        session['user_id'] = user['user_id']
        session['role'] = user['role']

        # ROLE CHECK
        if user['role'] == 'admin':
            return redirect(url_for('verification.admin_verification'))

        elif user['role'] == 'user':
            return redirect(url_for('verification.verification'))

        else:
            error = "Unknown role detected"
            return render_template('login.html', error=error)

    return render_template('login.html', error=error)


# Logout
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
