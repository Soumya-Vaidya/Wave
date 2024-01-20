import pickle
import re

import bcrypt
from flask import redirect, render_template, request, url_for

from main import app
from models import Journal, User, db

salt = bcrypt.gensalt()


with app.app_context():
    db.create_all()


# Load the saved model
with open("model.pkl", "rb") as file:
    etc = pickle.load(file)

# Load the saved vectorizer
with open("vectorizer.pkl", "rb") as file:
    vectorizer = pickle.load(file)


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("index.html")
    else:
        email = request.form["email"]
        passw = request.form["passwd"]
        passw = passw.encode()
        usr = User.query.filter_by(email=email).first()
        if usr is None:
            return "User Not Found"
        if bcrypt.checkpw(passw, usr.password):
            return redirect(url_for("home", user_id=usr.user_id))
        return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        email = request.form["email"]
        usr = User.query.filter_by(email=email).first()
        if usr:
            return "Email already Exists"

        passw = request.form["passwd"]
        name = request.form["name"]

        passw = passw.encode()
        hashed_password = bcrypt.hashpw(passw, salt)
        db.session.add(User(name=name, email=email, password=hashed_password))
        db.session.commit()
        return redirect("/")


@app.route("/home/<user_id>", methods=["GET", "POST"])
def home(user_id):
    if request.method == "GET":
        return render_template("home.html", user_id=user_id)
    elif request.method == "POST":
        entry = request.form["entry"]

        sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", entry)
        emotion_list = []
        for sentence in sentences:
            # processed_sentence = preprocess_function(sentence)
            sentence_vectorized = vectorizer.transform([sentence])
            emotion_prediction = etc.predict(sentence_vectorized)[0]
            emotion_list.append(emotion_prediction)

        journal = Journal(
            user_id=user_id,
            entry=entry,
            emotions=",".join(emotion_list),
            stress_level="1000",
            word_count="2000000",
        )
        db.session.add(journal)
        db.session.commit()
        print("Entry added")

        return redirect(url_for("home", user_id=user_id))
