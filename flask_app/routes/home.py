from flask import Blueprint, render_template, redirect, url_for, session

home_bp = Blueprint('home', __name__)

# Landing Page
@home_bp.route('/')
def home():
    return render_template('index.html')
