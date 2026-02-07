from flask import Flask
from routes.home import home_bp
from routes.auth import auth_bp
from routes.verification import verification_bp
from routes.directory import directory_bp
from routes.learning import learning_bp
from routes.statistics import statistics_bp

app = Flask(__name__)
app.secret_key = "secret_key"

# Register Blueprints
app.register_blueprint(home_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(verification_bp)
app.register_blueprint(directory_bp)
app.register_blueprint(learning_bp)
app.register_blueprint(statistics_bp)

if __name__ == '__main__':
    app.run(debug=True)
