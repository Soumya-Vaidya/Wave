from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, template_folder="templates")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)
# db.init_app(app)
# db.create_all()
# with app.app_context():
#     db.create_all()


from controllers import *

if __name__ == "__main__":
    app.run(debug=True, port=8081)