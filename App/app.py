from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta

app = Flask(__name__, template_folder="templates")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "your-secret-key"
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_CSRF_IN_COOKIES"] = False
app.config["JWT_COOKIE_CSRF_PROTECT"] = False


db = SQLAlchemy(app)
# db.init_app(app)
# db.create_all()
# with app.app_context():
#     db.create_all()


from controllers import *

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
