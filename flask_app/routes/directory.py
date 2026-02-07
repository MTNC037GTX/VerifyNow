from flask import Blueprint, render_template, request, redirect, url_for, session
from db import get_db

directory_bp = Blueprint('directory', __name__)


# User: view directory
@directory_bp.route('/directory')
def directory():
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Pagination variables
    page = int(request.args.get('page', 1))       # current page
    per_page = 10                                 # items per page
    offset = (page - 1) * per_page
    
    # Search and filter
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    
    where_clauses = ["is_hidden = 0"]
    params = []

    if search:
        where_clauses.append("fd.site_domain LIKE %s")
        params.append(f"%{search}%")

    if category:
        where_clauses.append("fd.category = %s")
        params.append(category)
        
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""


    db = get_db()
    cursor = db.cursor(dictionary=True)
    query = f"""
        SELECT fd.directory_id,
               fd.site_domain,
               fd.category,
               fd.risk_level,
               fd.date_reported,
               fd.reason
        FROM fake_directory fd
        {where_sql}
        ORDER BY fd.directory_id DESC
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, (*params, per_page, offset))
    directory_list = cursor.fetchall()
    
    # Count total number of directory
    count_query = f"SELECT COUNT(*) AS total FROM fake_directory fd {where_sql}"
    cursor.execute(count_query, params)
    total_items = cursor.fetchone()['total']
    total_pages = (total_items + per_page - 1) // per_page
    
    # Category → Icon mapping
    category_icons = {
        "Scam": "fa-triangle-exclamation",
        "News": "fa-newspaper",
        "Gambling": "fa-dice",
        "Ecommerce": "fa-cart-shopping",
        "Social": "fa-users",
        "Government": "fa-landmark",
        "Malware": "fa-bug",
        "Others": "fa-circle-question"
    }
    
    risk_classes = {
        "High": "fake",
        "Medium": "suspicious",
        "Low": "legit"
    }
    
    for row in directory_list:
        rl = (row.get('risk_level') or '')
        row['risk_class'] = risk_classes.get(rl, '')
        
        
    cursor.close()
    db.close()
    return render_template(
        'directory.html',
        directory_list=directory_list,
        page=page,
        total_pages=total_pages,
        total_items=total_items,
        category_icons=category_icons,
        risk_classes=risk_classes,
        search=search,
        category=category
        )



# Admin: view directory
@directory_bp.route('/admin-directory')
def admin_directory():
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    if session.get('role') != 'admin':
        return redirect(url_for('directory.directory'))
    
    
    # Pagination variables
    page = int(request.args.get('page', 1))       # current page
    per_page = 10                                 # items per page
    offset = (page - 1) * per_page
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT fd.directory_id,
                fd.site_domain,
                fd.category,
                fd.risk_level,
                fd.date_reported,
                fd.is_hidden,
                fd.reason
        FROM fake_directory fd
        ORDER BY fd.directory_id DESC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    directory_list = cursor.fetchall()
    
    # Count total number of directory
    cursor.execute("SELECT COUNT(*) AS total FROM fake_directory")
    total_items = cursor.fetchone()['total']
    total_pages = (total_items + per_page - 1) // per_page
    
    # Category → Icon mapping
    category_icons = {
        "Scam": "fa-triangle-exclamation",
        "News": "fa-newspaper",
        "Gambling": "fa-dice",
        "Ecommerce": "fa-cart-shopping",
        "Social": "fa-users",
        "Government": "fa-landmark",
        "Malware": "fa-bug",
        "Others": "fa-circle-question"
    }
    
    # Risk Level Colors
    risk_classes = {
        "High": "fake",
        "Medium": "suspicious",
        "Low": "legit"
    }
    
    for row in directory_list:
        rl = (row.get('risk_level') or '')
        row['risk_class'] = risk_classes.get(rl, '')
    
    cursor.close()
    db.close()
    return render_template(
        'admin-directory.html',
        directory_list=directory_list, 
        page=page, 
        total_pages=total_pages,
        total_items=total_items,
        category_icons=category_icons,
        risk_classes=risk_classes
        )
    
    
    
# Admin adds a new directory entry
@directory_bp.route('/add-directory', methods=['POST'])
def add_directory():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    site_domain = request.form['site_domain']
    category = request.form['category']
    risk_level = request.form['risk_level']
    reason = request.form['reason']

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO fake_directory (site_domain, category, risk_level,reason, date_reported)
        VALUES (%s, %s, %s, %s, NOW())
    """, (site_domain, category, risk_level, reason))

    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('directory.admin_directory'))



# Admin deletes a directory entry
@directory_bp.route('/delete-directory/<int:directory_id>', methods=['POST'])
def delete_directory(directory_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("DELETE FROM fake_directory WHERE directory_id = %s", (directory_id,))
    db.commit()
    
    cursor.close()
    db.close()
    
    return redirect(url_for('directory.admin_directory'))



# Admin hide directory
@directory_bp.route("/toggle-directory-visibility/<int:directory_id>", methods=["POST"])
def toggle_directory_visibility(directory_id):
    db = get_db()
    cursor = db.cursor()

    # Fetch current state
    cursor.execute("SELECT is_hidden FROM fake_directory WHERE directory_id = %s", (directory_id,))
    row = cursor.fetchone()
    if not row:
        return "Directory not found", 404

    current_state = row[0]
    new_state = 0 if current_state == 1 else 1

    # Update DB
    cursor.execute("UPDATE fake_directory SET is_hidden = %s WHERE directory_id = %s", (new_state, directory_id))
    db.commit()
    cursor.close()

    return redirect(url_for("directory.admin_directory"))
