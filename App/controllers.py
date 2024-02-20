import pickle
import re

import bcrypt
from flask import redirect, render_template, request, url_for

from app import app
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

# Load the saved stress model
with open("stress_model.pkl", "rb") as file:
    stress = pickle.load(file)

# Load the saved stress vectorizer
with open("stress_vectorizer.pkl", "rb") as file:
    stress_vectorizer = pickle.load(file)


@app.route("/", methods=["GET", "POST"])
def landing():
    if request.method == "GET":
        return render_template("landing.html")
    else:
        return render_template("404_error.html")


@app.route("/Wave/login", methods=["GET", "POST"])
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


@app.route("/Wave/register", methods=["GET", "POST"])
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


@app.route("/Wave/home/<user_id>", methods=["GET", "POST"])
def home(user_id):
    if request.method == "GET":
        journals = Journal.query.filter_by(user_id=user_id).all()
        return render_template("home.html", user_id=user_id, journals=journals)
    elif request.method == "POST":
        entry = request.form["entry"]
        word_count = entry.count(" ") + 1
        sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", entry)
        emotion_list = []
        avg_stress = 0
        for sentence in sentences:
            # processed_sentence = preprocess_function(sentence)
            sentence_vectorized = vectorizer.transform([sentence])
            emotion_prediction = etc.predict(sentence_vectorized)[0]
            emotion_list.append(emotion_prediction)

        entry_vectorized = stress_vectorizer.transform([entry])
        stress_prediction = stress.predict(entry_vectorized)[0]

        journal = Journal(
            user_id=user_id,
            entry=entry,
            emotions=",".join(emotion_list),
            stress_level=str(stress_prediction),
            word_count=word_count,
        )
        db.session.add(journal)
        db.session.commit()
        print("Entry added")

        return redirect(url_for("home", user_id=user_id))


@app.route("/Wave/<user_id>/<entry_id>", methods=["GET", "POST"])
def entry(user_id, entry_id):
    if request.method == "GET":
        entry = Journal.query.filter_by(jid=entry_id).first()
        return render_template("entry.html", entry=entry)


@app.route("/Wave/<user_id>/profile", methods=["GET", "POST"])
def view_profile(user_id):
    if request.method == "GET":
        user = User.query.filter_by(user_id=user_id).first()
        return render_template("view_profile.html", user=user)
    else:
        return render_template("404_error.html")


@app.route("/Wave/<user_id>/profile/edit", methods=["GET", "POST"])
def edit_profile(user_id):
    if request.method == "GET":
        user = User.query.filter_by(user_id=user_id).first()
        return render_template("edit_profile.html", user=user)
    elif request.method == "POST":
        name = request.form["name"]
        try:
            # user = User.query.filter_by(user_id=user_id).first()
            user = db.session.query(User).get(user_id)
            user.name = name
        except:
            db.session.rollback()
        else:
            db.session.commit()
            print("getting commited")
            return redirect(url_for("view_profile", user_id=user_id))
