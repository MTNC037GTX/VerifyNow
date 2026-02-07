from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from db import get_db

statistics_bp = Blueprint('statistics', __name__)


# User: statistics page
@statistics_bp.route('/statistics')
def statistics():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    cursor = db.cursor()
    
    
    # Total verifications (Label A)
    cursor.execute("SELECT COUNT(*) FROM verification_result")
    total_verifications = cursor.fetchone()[0]

    # Suspicious / Fake (Label B)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM verification_result
        WHERE result IN ('suspicious', 'fake')
    """)
    suspicious_count = cursor.fetchone()[0]


    # Websites added to Fake Directory (Label C)
    cursor.execute("SELECT COUNT(*) FROM fake_directory")
    directory_count = cursor.fetchone()[0]


    # Source Reliability Rating (Label D)
    cursor.execute("""
        SELECT source_name, reliability_score
        FROM source_reliability
        ORDER BY reliability_score DESC
    """)
    sr_rows = cursor.fetchall()
    source_labels = [row[0] for row in sr_rows]
    source_scores = [row[1] for row in sr_rows]


    # Risk Level Distribution (Label E)
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN risk_level = 'Low' THEN 1 ELSE 0 END),
            SUM(CASE WHEN risk_level = 'Medium' THEN 1 ELSE 0 END),
            SUM(CASE WHEN risk_level = 'High' THEN 1 ELSE 0 END)
        FROM fake_directory 
        WHERE is_hidden = 0
    """)
    low, medium, high = cursor.fetchone()


    # Top Reported Domains (from top_reported table)
    cursor_tr = db.cursor(dictionary=True)
    cursor_tr.execute("""
        SELECT tr.top_domain_id,
               tr.top_name,
               tr.report_count,
               tr.category
        FROM top_reported tr
        ORDER BY tr.report_count DESC
    """)
    top_reported = cursor_tr.fetchall()
    
    categories = {
        "Beginner Guide": "blue",
        "Fake News": "green",
        "Phishing": "purple"
    }
    
    for row in top_reported:
        rl = (row.get('category') or '')
        row['category_tag'] = categories.get(rl, '')
        
    # Ranking
    for index, row in enumerate(top_reported, start=1):
        row["rank"] = index

        # Top 3 badges
        if index == 1:
            row["rank_badge"] = "gold"
        elif index == 2:
            row["rank_badge"] = "silver"
        elif index == 3:
            row["rank_badge"] = "bronze"
        else:
            row["rank_badge"] = "normal"

        # Risk level based on report_count
        count = row.get("report_count", 0)
        if count >= 50:
            row["risk_level"] = "High"
            row["risk_class"] = "fake"
        elif count >= 20:
            row["risk_level"] = "Medium"
            row["risk_class"] = "suspicious"
        else:
            row["risk_level"] = "Low"
            row["risk_class"] = "legit"
    

    return render_template(
        "statistics.html",
        total_verifications=total_verifications,
        suspicious_count=suspicious_count,
        directory_count=directory_count,

        source_labels=source_labels,
        source_scores=source_scores,

        risk_low=low or 0,
        risk_medium=medium or 0,
        risk_high=high or 0,

        top_reported=top_reported,
        categories=categories
    )



# Admin: statistics management page
@statistics_bp.route('/admin-statistics')
def admin_statistics():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if session.get('role') != 'admin':
        return redirect(url_for('statistics.statistics'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Total verifications (Label A)
    cursor.execute("SELECT COUNT(*) FROM verification_result")
    total_verifications = cursor.fetchone()[0]

    # Suspicious / Fake (Label B)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM verification_result
        WHERE result IN ('suspicious', 'fake')
    """)
    suspicious_count = cursor.fetchone()[0]

    # Websites added to Fake Directory (Label C)
    cursor.execute("SELECT COUNT(*) FROM fake_directory")
    directory_count = cursor.fetchone()[0]

    # Source Reliability Rating (Label D)
    cursor.execute("""
        SELECT source_id, source_name, reliability_score
        FROM source_reliability
        ORDER BY reliability_score DESC
    """)

    sr_rows = cursor.fetchall()

    source_labels = [row[1] for row in sr_rows]
    source_scores = [row[2] for row in sr_rows]

    # Pass source_reliability as a list of dicts for Jinja2
    source_reliability = [
        {"id": row[0], "source": row[1], "reliability": row[2]}
        for row in sr_rows
    ]

    # Risk Level Distribution (Label E)
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN risk_level = 'Low' THEN 1 ELSE 0 END),
            SUM(CASE WHEN risk_level = 'Medium' THEN 1 ELSE 0 END),
            SUM(CASE WHEN risk_level = 'High' THEN 1 ELSE 0 END)
        FROM fake_directory
        WHERE is_hidden = 0
    """)
    low, medium, high = cursor.fetchone()

    # Top Reported Domains
    cursor_tr = db.cursor(dictionary=True)
    cursor_tr.execute("""
        SELECT top_domain_id, top_name, report_count, category
        FROM top_reported
        ORDER BY report_count DESC
    """)
    top_reported = cursor_tr.fetchall()
    
    cursor_tr.close()
    cursor.close()
    db.close()
    
    return render_template(
        "admin-statistics.html",
        total_verifications=total_verifications,
        suspicious_count=suspicious_count,
        directory_count=directory_count,

        source_labels=source_labels,
        source_scores=source_scores,
        source_reliability=source_reliability, 

        risk_low=low or 0,
        risk_medium=medium or 0,
        risk_high=high or 0,

        top_reported=top_reported
    )


# Admin: update statistics
@statistics_bp.route('/admin-statistics/update', methods=['POST'])
def update_admin_statistics():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if session.get('role') != 'admin':
        return redirect(url_for('statistics.statistics'))

    db = get_db()
    cursor = db.cursor()

    # ---------- SOURCE RELIABILITY ----------
    source_names = request.form.getlist('source_name[]')
    reliability_scores = request.form.getlist('reliability_score[]')

    cursor.execute("DELETE FROM source_reliability")

    for i in range(len(source_names)):
        name = source_names[i].strip()
        score = reliability_scores[i].strip()

        if name != '' and score != '':
            cursor.execute(
                """
                INSERT INTO source_reliability (source_name, reliability_score)
                VALUES (%s, %s)
                """,
                (name, score)
            )

    # ---------- TOP REPORTED DOMAINS ----------
    domain_names = request.form.getlist('top_name[]')
    report_counts = request.form.getlist('report_count[]')
    categories = request.form.getlist('category[]')

    cursor.execute("DELETE FROM top_reported")

    for i in range(len(domain_names)):
        domain = domain_names[i].strip()
        count = report_counts[i].strip()
        category = categories[i].strip()

        if domain != '' and count != '' and category != '':
            cursor.execute(
                """
                INSERT INTO top_reported (top_name, report_count, category)
                VALUES (%s, %s, %s)
                """,
                (domain, count, category)
            )

    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('statistics.admin_statistics'))
