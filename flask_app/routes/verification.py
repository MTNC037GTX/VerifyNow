from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db
from model import verify_url_logic

verification_bp = Blueprint('verification', __name__)


# =========================
# USER: SUBMIT CONTENT
# =========================
@verification_bp.route('/submit_content', methods=['POST'])
def submit_content():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    body_text = request.form.get('body_text', '').strip()
    if not body_text:
        flash("No content submitted", "error")
        return redirect(url_for('verification.verification'))

    is_url = body_text.startswith(("http://", "https://"))

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO Content (user_id, body_text, status)
        VALUES (%s, %s, 'Pending')
    """, (session['user_id'], body_text))

    db.commit()
    cursor.close()
    db.close()

    flash("Content submitted for verification", "success")

    return redirect(
        url_for(
            'verification.verification',
            active_tab='url' if is_url else 'text'
        )
    )


# =========================
# USER: VIEW VERIFICATIONS
# =========================
@verification_bp.route('/verification')
def verification():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT c.content_id,
               c.body_text,
               vr.result,
               vr.confidence_score,
               vr.remarks,
               c.date
        FROM Content c
        LEFT JOIN Verification_Result vr ON c.content_id = vr.content_id
        WHERE c.user_id = %s
        ORDER BY c.content_id DESC
        LIMIT %s OFFSET %s
    """, (user_id, per_page, offset))
    results = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM Content
        WHERE user_id = %s
    """, (user_id,))
    total_items = cursor.fetchone()['total']
    total_pages = (total_items + per_page - 1) // per_page

    for row in results:
        if row['result'] == "Fake":
            row['result_class'] = "fake"
        elif row['result'] == "Suspicious":
            row['result_class'] = "suspicious"
        elif row['result'] == "Legit":
            row['result_class'] = "legit"
        else:
            row['result_class'] = ""

    selected_id = request.args.get("content_id")
    selected_item = None

    if selected_id:
        cursor.execute("""
            SELECT c.body_text,
                   vr.result,
                   vr.confidence_score,
                   vr.remarks
            FROM Content c
            LEFT JOIN Verification_Result vr ON c.content_id = vr.content_id
            WHERE c.content_id = %s
        """, (selected_id,))
        selected_item = cursor.fetchone()

        if selected_item:
            result = selected_item.get("result")
            if result == "Fake":
                selected_item.update({
                    "icon_class": "fa-solid fa-triangle-exclamation",
                    "icon_color": "#991B1B",
                    "icon_bg": "#FEE2E2"
                })
            elif result == "Suspicious":
                selected_item.update({
                    "icon_class": "fa-solid fa-exclamation",
                    "icon_color": "#854D0E",
                    "icon_bg": "#FEF9C3"
                })
            elif result == "Legit":
                selected_item.update({
                    "icon_class": "fa-solid fa-check",
                    "icon_color": "#166534",
                    "icon_bg": "#DCFCE7"
                })
            else:
                selected_item.update({
                    "icon_class": "fa-solid fa-clock",
                    "icon_color": "#6B7280",
                    "icon_bg": "#f3f4f6"
                })

    cursor.close()
    db.close()

    return render_template(
        'verification.html',
        results=results,
        page=page,
        total_pages=total_pages,
        total_items=total_items,
        selected_item=selected_item,
        active_tab=request.args.get("active_tab")
    )


# =========================
# ADMIN: VIEW & RUN ML
# =========================
@verification_bp.route('/admin-verification', methods=['GET'])
def admin_verification():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'admin':
        return redirect(url_for('verification.verification'))

    # =========================
    # INPUTS
    # =========================
    content_id = request.args.get('content_id')
    ml_url = request.args.get('ml_url')

    ml_result = None
    submitted_content = None

    # =========================
    # PAGINATION
    # =========================
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # =========================
    # CONTENT LIST
    # =========================
    cursor.execute("""
        SELECT c.content_id,
               c.body_text,
               c.status,
               vr.result,
               vr.confidence_score,
               vr.verification_date
        FROM Content c
        LEFT JOIN Verification_Result vr
            ON c.content_id = vr.content_id
        ORDER BY c.content_id DESC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    content_list = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS total FROM Content")
    total_items = cursor.fetchone()['total']
    total_pages = (total_items + per_page - 1) // per_page

    # =========================
    # ADMIN MANUAL ML VERIFY
    # =========================
    if ml_url:
        submitted_content = ml_url.strip()

        if submitted_content.startswith(("http://", "https://")):
            try:
                ml_result = verify_url_logic(submitted_content)
            except Exception as e:
                print("ADMIN ML ERROR:", e)
                ml_result = {
                    "domain": "invalid",
                    "credibility_score": 0.0,
                    "trust": 0,
                    "label": "fake"
                }

    # =========================
    # VERIFY FROM CONTENT TABLE
    # =========================
    elif content_id:
        cursor.execute("""
            SELECT body_text
            FROM Content
            WHERE content_id = %s
        """, (content_id,))
        row = cursor.fetchone()

        if row:
            submitted_content = row['body_text'].strip()

            if submitted_content.startswith(("http://", "https://")):
                try:
                    ml_result = verify_url_logic(submitted_content)
                except Exception as e:
                    print("CONTENT ML ERROR:", e)
                    ml_result = {
                        "domain": "invalid",
                        "credibility_score": 0.0,
                        "trust": 0,
                        "label": "fake"
                    }

    # =========================
    # RESULT LABEL STYLING
    # =========================
    for row in content_list:
        result = row.get('result')
        if result == "Fake":
            row['result_class'] = "fake"
        elif result == "Suspicious":
            row['result_class'] = "suspicious"
        elif result == "Legit":
            row['result_class'] = "legit"
        else:
            row['result_class'] = ""

    cursor.close()
    db.close()

    return render_template(
        'admin-verification.html',
        content_list=content_list,
        submitted_content=submitted_content,
        ml_result=ml_result,
        page=page,
        total_pages=total_pages,
        total_items=total_items
    )




# =========================
# ADMIN: FINAL DECISION
# =========================
@verification_bp.route('/admin-verify/<int:content_id>', methods=['POST'])
def verify_content(content_id):
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    result = request.form['result']
    confidence_score = request.form['confidence_score']
    remarks = request.form['remarks']

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO Verification_Result
        (content_id, result, confidence_score, remarks, verification_date)
        VALUES (%s, %s, %s, %s, CURDATE())
    """, (content_id, result, confidence_score, remarks))

    cursor.execute("""
        UPDATE Content
        SET status = 'Verified'
        WHERE content_id = %s
    """, (content_id,))

    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('verification.admin_verification'))
