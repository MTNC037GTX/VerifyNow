import os
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from db import get_db

learning_bp = Blueprint('learning', __name__)

# User: learning page
@learning_bp.route('/learning')
def learning():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM article WHERE is_hidden = 0 ORDER BY publish_date DESC")
    articles = cursor.fetchall()
    
    # Thumbnail image
    upload_dir = os.path.join(current_app.static_folder, "uploads")

    for article in articles:
        file_name = article.get("thumbnail_image", "")

        # Full path to the image
        full_path = os.path.join(upload_dir, file_name) if file_name else ""

        # Check existence — fallback to placeholder if missing
        if (not file_name) or (not os.path.isfile(full_path)):
            article["thumbnail_image"] = "placeholder.jpg"

    cursor.close()
    db.close()

    return render_template("learning.html", articles=articles)


# User: Article page
# View an article
@learning_bp.route('/article/<int:article_id>')
def view_article(article_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT title, description, category, content, thumbnail_image
        FROM article
        WHERE article_id = %s
    """, (article_id,))
    article = cursor.fetchone()
    cursor.close()
    db.close()

    if not article:
        return "Article not found", 404

    return render_template('article.html', article=article)



# Admin: learning management page
@learning_bp.route('/admin-learning')
def admin_learning():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if session.get('role') != 'admin':
        return redirect(url_for('learning.learning'))
    
    
    # Pagination variables
    page = int(request.args.get('page', 1))       # current page
    per_page = 10                                 # items per page
    offset = (page - 1) * per_page
    

    db = get_db()
    cursor = db.cursor(dictionary=True)
    query = """
        SELECT a.article_id,
               a.title,
               a.description,
               a.category,
               a.content,
               a.thumbnail_image,
               a.publish_date,
               a.is_hidden
        FROM article a
        ORDER BY a.article_id DESC
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, (per_page, offset))
    article_list = cursor.fetchall()
    
    # Count total number of articles
    count_query = "SELECT COUNT(*) AS total FROM article a"
    cursor.execute(count_query)
    total_items = cursor.fetchone()['total']
    total_pages = (total_items + per_page - 1) // per_page
    
    
    categories = {
        "Beginner Guide": "blue",
        "Cybersecurity": "green",
        "Infographic": "purple"
    }
    
    for row in article_list:
        rl = (row.get('category') or '')
        row['category_tag'] = categories.get(rl, '')
    
    cursor.close()
    db.close()
    return render_template(
        'admin-learning.html',
        article_list=article_list,
        page=page,
        total_pages=total_pages,
        total_items=total_items,
        categories=categories
        )
    
    
    
# Admin adds a new article
@learning_bp.route('/add-article', methods=['POST'])
def add_article():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    title = request.form['title']
    description = request.form['description']
    category = request.form['category']
    content = request.form['content']
    
     # File upload
    thumbnail = request.files.get('thumbnail_image')

    if thumbnail and thumbnail.filename != "":
        UPLOAD_FOLDER = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        file_path = os.path.join(UPLOAD_FOLDER, thumbnail.filename)
        thumbnail.save(file_path)

        thumbnail_filename = thumbnail.filename
    else:
        thumbnail_filename = None

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO article (title, description, category, content, thumbnail_image, publish_date)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """, (title, description, category, content, thumbnail_filename))

    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('learning.admin_learning'))



# Admin edit article
@learning_bp.route("/update-article", methods=["POST"])
def update_article():
    article_id = request.form.get("article_id")
    
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # 1. Get existing article data
    cursor.execute("SELECT * FROM article WHERE article_id = %s", (article_id,))
    article = cursor.fetchone()
    if not article:
        return "Article not found", 404

    # 2. Get updated fields
    title = request.form.get('title')
    description = request.form.get('description')
    category = request.form.get('category')
    content = request.form.get('content')

    # 3. Handle thumbnail upload using the EXACT logic you provided
    thumbnail = request.files.get('thumbnail_image')

    if thumbnail and thumbnail.filename != "":
        UPLOAD_FOLDER = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        file_path = os.path.join(UPLOAD_FOLDER, thumbnail.filename)
        thumbnail.save(file_path)

        thumbnail_filename = thumbnail.filename
    else:
        thumbnail_filename = article['thumbnail_image']  # keep old
        

    # 4. Update DB record
    cursor.execute("""
        UPDATE article
        SET title = %s,
            description = %s,
            category = %s,
            content = %s,
            thumbnail_image = %s
        WHERE article_id = %s
    """, (
        title,
        description,
        category,
        content,
        thumbnail_filename,
        article_id
    ))

    db.commit()
    cursor.close() 
    return redirect(url_for("learning.admin_learning"))



# Admin hide article
@learning_bp.route("/toggle-article-visibility/<int:article_id>", methods=["POST"])
def toggle_article_visibility(article_id):
    db = get_db()
    cursor = db.cursor()

    # Fetch current state
    cursor.execute("SELECT is_hidden FROM article WHERE article_id = %s", (article_id,))
    row = cursor.fetchone()
    if not row:
        return "Article not found", 404

    current_state = row[0]
    new_state = 0 if current_state == 1 else 1

    # Update DB
    cursor.execute("UPDATE article SET is_hidden = %s WHERE article_id = %s", (new_state, article_id))
    db.commit()
    cursor.close()

    return redirect(url_for("learning.admin_learning"))

