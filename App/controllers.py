import pickle
import re

from transformers import pipeline

import bcrypt
from flask import redirect, render_template, request, url_for, json

from datetime import datetime

import pytz

IST = pytz.timezone("Asia/Kolkata")

from app import app
from models import Journal, User, Emotions, db

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

with open("dl_model.pkl", "rb") as file:
    model = pickle.load(file)


@app.route("/", methods=["GET", "POST"])
def landing():
    if request.method == "GET":
        return render_template("landing.html")
    else:
        return render_template("404_error.html")


@app.route("/Wave/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        email = request.form["email"]
        passw = request.form["password"]
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

        passw = request.form["password"]
        name = request.form["name"]
        gender = request.form["gender"]
        age = request.form["age"]
        emergency_contact = request.form["emergency_contact"]
        contact = request.form["contact"]
        profile_picture = request.form["profile_picture"]

        passw = passw.encode()
        hashed_password = bcrypt.hashpw(passw, salt)
        db.session.add(
            User(
                name=name,
                email=email,
                password=hashed_password,
                gender=gender,
                age=age,
                emergency_contact=emergency_contact,
                contact=contact,
                profile_picture=profile_picture,
            )
        )
        db.session.commit()
        return redirect("/")


@app.route("/Wave/home/<user_id>", methods=["GET", "POST"])
def home(user_id):
    if request.method == "GET":
        user = User.query.filter_by(user_id=user_id).first()
        date_format = datetime.now(IST).strftime("%dth %B, %Y")
        date = datetime.now(IST).date()
        today_journal = Journal.query.filter_by(user_id=user_id, date=date).first()
        if today_journal:
            journals = Journal.query.filter_by(user_id=user_id).all()
            emotions = Emotions.query.filter_by(jid=today_journal.jid).all()
            label = json.dumps([emotion.emotion_name for emotion in emotions])
            data = json.dumps([emotion.value for emotion in emotions])
            print(label)
            print(data)
        else:
            journals = ""
            emotions = ""
            label = ""
            data = ""
        print(emotions)

        return render_template(
            "today.html",
            user=user,
            journals=journals,
            today_journal=today_journal,
            date=date_format,
            emotions=emotions,
            label=label,
            data=data,
        )
    elif request.method == "POST":
        entry = request.form["entry"]
        word_count = entry.count(" ") + 1

        emotions = model.predict(entry)[0]
        # print(emotions)
        # filters acc to threshold from DL model
        filtered_emotions = [emotion for emotion in emotions if emotion["score"] > 0.1]
        top_5_emotions = sorted(
            filtered_emotions, key=lambda x: x["score"], reverse=True
        )[:5]
        emotion_dict = {
            emotion["label"]: emotion["score"] for emotion in top_5_emotions
        }
        print(emotion_dict)

        # predict using our ML model
        sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", entry)
        emotion_list = []
        for sentence in sentences:
            # processed_sentence = preprocess_function(sentence)
            sentence_vectorized = vectorizer.transform([sentence])
            emotion_prediction = etc.predict(sentence_vectorized)[0]
            emotion_list.append(emotion_prediction)

        # Stress Detection
        entry_vectorized = stress_vectorizer.transform([entry])
        stress_prediction = stress.predict(entry_vectorized)[0]

        date = datetime.now(IST).date()

        journal = Journal.query.filter_by(user_id=user_id, date=date).first()
        # if journal entry already exists, update it
        if journal:
            try:
                journal.entry = entry
                journal.emotions = ",".join(emotion_list)
                journal.stress_level = str(stress_prediction)
                journal.word_count = word_count
                journal.date = date
                db.session.commit()
                print("Entry updated")

                emotions = Emotions.query.filter_by(jid=journal.jid).all()
                for emotion in emotions:
                    db.session.delete(emotion)
                db.session.commit()
                for emotion_name, emotion_value in emotion_dict.items():
                    emotion = Emotions(
                        jid=journal.jid, emotion_name=emotion_name, value=emotion_value
                    )
                    db.session.add(emotion)
                db.session.commit()

            except:
                db.session.rollback()
        # if new entry for the day
        else:
            journal = Journal(
                user_id=user_id,
                entry=entry,
                emotions=",".join(emotion_list),
                stress_level=str(stress_prediction),
                word_count=word_count,
                date=date,
            )
            db.session.add(journal)
            db.session.commit()

            for emotion_name, emotion_value in emotion_dict.items():
                emotion = Emotions(
                    jid=journal.jid, emotion_name=emotion_name, value=emotion_value
                )
                db.session.add(emotion)
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
        return render_template("profile.html", user=user)
    else:
        return render_template("404_error.html")


@app.route("/Wave/<user_id>/profile/edit", methods=["GET", "POST"])
def edit_profile(user_id):
    if request.method == "GET":
        user = User.query.filter_by(user_id=user_id).first()
        return render_template("profile.html", user=user)
    elif request.method == "POST":
        name = request.form["name"]
        contact = request.form["contact"]
        emergency_contact = request.form["emergency_contact"]
        age = request.form["age"]
        gender = request.form["gender"]
        try:
            # user = User.query.filter_by(user_id=user_id).first()
            user = db.session.query(User).get(user_id)
            user.name = name
            user.contact = contact
            user.emergency_contact = emergency_contact
            user.age = age
            user.gender = gender
        except:
            db.session.rollback()
        else:
            db.session.commit()
            print("getting commited")
            return redirect(url_for("view_profile", user_id=user_id))
