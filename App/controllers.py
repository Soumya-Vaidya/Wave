import pickle
import re

from transformers import pipeline

import bcrypt
from flask import redirect, render_template, request, url_for, json, jsonify

import pytz

IST = pytz.timezone("Asia/Kolkata")

from app import app
from models import Journal, User, Emotions, db
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from datetime import date


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


def streak(user_id):
    journals = Journal.query.filter_by(user_id=user_id).all()
    continuous_days = 0
    previous_date = None

    # journals.sort(key=lambda x: x.date).reverse()

    journals.sort(key=lambda x: x.date, reverse=True)

    today = datetime.now(IST).date()
    today_journal = Journal.query.filter_by(user_id=user_id, date=today).first()

    yesterday = today - timedelta(days=1)
    yesterday_journal = Journal.query.filter_by(user_id=user_id, date=yesterday).first()

    if today_journal is None and yesterday_journal is None:
        return 0

    continuous_days = 0
    previous_date = None

    for journal in journals:
        if previous_date is None:
            continuous_days += 1
        elif journal.date == previous_date - timedelta(days=1):
            continuous_days += 1
        else:
            break
        previous_date = journal.date

    return continuous_days


def longest_streak(user_id):
    journals = Journal.query.filter_by(user_id=user_id).all()
    longest_continuous_days = 0
    current_continuous_days = 0
    previous_date = None

    for journal in journals:
        current_date = journal.date
        if previous_date is None or (current_date - previous_date).days == 1:
            current_continuous_days += 1
        else:
            current_continuous_days = 1

        if current_continuous_days > longest_continuous_days:
            longest_continuous_days = current_continuous_days

        previous_date = current_date

    return longest_continuous_days


@app.route("/Wave/<user_id>/home", methods=["GET", "POST"])
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

        else:
            journals = ""
            emotions = ""
            label = ""
            data = ""

        continuous_days = streak(user_id)

        return render_template(
            "today.html",
            user=user,
            journals=journals,
            today_journal=today_journal,
            date=date_format,
            emotions=emotions,
            label=label,
            data=data,
            continuous_days=continuous_days,
        )
    elif request.method == "POST":
        entry = request.form["entry"]
        word_count = entry.count(" ") + 1

        emotions = model.predict(entry)[0]

        # filters acc to threshold from DL model
        filtered_emotions = [emotion for emotion in emotions if emotion["score"] > 0.1]
        top_5_emotions = sorted(
            filtered_emotions, key=lambda x: x["score"], reverse=True
        )[:5]
        emotion_dict = {
            emotion["label"]: emotion["score"] for emotion in top_5_emotions
        }
        # print(emotion_dict)

        major_emotion = max(emotion_dict, key=emotion_dict.get)
        print(major_emotion)

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
                # update journal table
                journal.entry = entry
                # journal.emotions = ",".join(emotion_list)
                journal.emotions = major_emotion
                journal.stress_level = str(stress_prediction)
                journal.word_count = word_count
                journal.date = date
                db.session.commit()
                print("Entry updated")
                print(major_emotion)

                # update emotions table
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
            # add new entry to journal table
            journal = Journal(
                user_id=user_id,
                entry=entry,
                # emotions=",".join(emotion_list),
                emotions=major_emotion,
                stress_level=str(stress_prediction),
                word_count=word_count,
                date=date,
            )
            db.session.add(journal)
            db.session.commit()

            # add emotions to emotions table
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
        user = User.query.filter_by(user_id=user_id).first()
        entry = Journal.query.filter_by(jid=entry_id).first()
        if entry:
            emotions = Emotions.query.filter_by(jid=entry.jid).all()
            label = json.dumps([emotion.emotion_name for emotion in emotions])
            data = json.dumps([emotion.value for emotion in emotions])

        continuous_days = streak(user_id)
        print(continuous_days)

        return render_template(
            "entry.html",
            today_journal=entry,
            user=user,
            label=label,
            data=data,
            continuous_days=continuous_days,
        )


@app.route("/Wave/<user_id>/overview", methods=["GET", "POST"])
def overview(user_id):
    if request.method == "GET":
        user = User.query.filter_by(user_id=user_id).first()
        journals = Journal.query.filter_by(user_id=user_id).all()

        week_start = datetime.now(IST).date() - timedelta(days=7)
        week_journals = (
            Journal.query.filter_by(user_id=user_id)
            .filter(Journal.date >= week_start)
            .all()
        )

        # for journal in week_journals:
        #     journal.date = journal.date.strftime("%dth %B, %Y")

        # Get the first entry date in Journal
        first_entry = Journal.query.order_by(Journal.date).first()
        if first_entry:
            first_date = first_entry.date
        else:
            first_date = datetime.now(IST).date()

        # Create a list of all dates from the first entry date to the current date
        all_dates = [
            first_date + timedelta(days=i)
            for i in range((datetime.now(IST).date() - first_date).days + 1)
        ]

        calendar_rows = []
        for date in all_dates:
            date_str = date.strftime("%d")
            journal = Journal.query.filter_by(user_id=user_id, date=date).first()
            if journal:
                journal = Journal.query.filter_by(user_id=user_id, date=date).first()
            if journal:
                emotions = journal.emotions
                row = [(date_str, emotions)]
            else:
                row = [(date_str, "None")]
            calendar_rows.append(row)

        print(calendar_rows)

        continuous_days = streak(user_id)

        return render_template(
            "overview.html",
            user=user,
            journals=journals,
            week_journals=week_journals,
            calendar_rows=calendar_rows,
            continuous_days=continuous_days,
        )
    else:
        print("Error")


@app.route("/Wave/<user_id>/analytics", methods=["GET", "POST"])
def analytics(user_id):
    if request.method == "GET":
        user = User.query.filter_by(user_id=user_id).first()

        # Emotions Pie Chart
        journals = Journal.query.filter_by(user_id=user_id).all()
        emotions = []
        for journal in journals:
            emotions += Emotions.query.filter_by(jid=journal.jid).all()

        emotions_dict = {}
        for emotion in emotions:
            if emotion.emotion_name in emotions_dict:
                emotions_dict[emotion.emotion_name] += emotion.value
            else:
                emotions_dict[emotion.emotion_name] = emotion.value

        label = json.dumps(list(emotions_dict.keys()))
        data = json.dumps(list(emotions_dict.values()))

        # Total Word Count and Entries
        total_word_count = sum(journal.word_count for journal in journals)
        total_entries = Journal.query.filter_by(user_id=user_id).count()

        # Stress Level Pie Chart
        stress_count = Journal.query.filter_by(
            user_id=user_id, stress_level="Stress"
        ).count()
        no_stress_count = Journal.query.filter_by(
            user_id=user_id, stress_level="No Stress"
        ).count()

        stress_label = json.dumps(["Stress", "No Stress"])
        stress_data = json.dumps([stress_count, no_stress_count])

        # Count the longest number of continuous days with journal entries
        # longest_continuous_days = 0
        # current_continuous_days = 0
        # previous_date = None

        # for journal in journals:
        #     current_date = journal.date
        #     if previous_date is None or (current_date - previous_date).days == 1:
        #         current_continuous_days += 1
        #     else:
        #         current_continuous_days = 1

        #     if current_continuous_days > longest_continuous_days:
        #         longest_continuous_days = current_continuous_days

        #     previous_date = current_date

        longest_continuous_days = longest_streak(user_id)

        # Count the number of continuous days since today in the journal table
        # continuous_days = 0  # if there is some error, this used to be 0
        # previous_date = None

        # for journal in journals:
        #     if previous_date is None:
        #         continuous_days += 1
        #     elif journal.date == previous_date - timedelta(days=1):
        #         continuous_days += 1
        #     else:
        #         break
        #     previous_date = journal.date

        continuous_days = streak(user_id)

        # Last month word count Line Chart
        last_month_start = datetime.now(IST).date() - timedelta(days=30)
        last_month_journals = (
            Journal.query.filter_by(user_id=user_id)
            .filter(Journal.date >= last_month_start)
            .all()
        )

        word_counts = []
        last_month_dates = []

        for i in range(30):
            date = (datetime.now(IST).date() - timedelta(days=i)).strftime(
                "%dth %B, %Y"
            )
            last_month_dates.append(date)

            found_journal = False
            for journal in last_month_journals:
                if journal.date.strftime("%dth %B, %Y") == date:
                    word_counts.append(journal.word_count)
                    found_journal = True
                    break

            if not found_journal:
                word_counts.append(0)

        word_counts.reverse()
        last_month_dates.reverse()

        # count of stress and no stress for each emotion
        emotions_stress_counts = {}

        emotions_count = {}
        for journal in journals:
            if journal.emotions in emotions_count:
                emotions_count[journal.emotions] += 1
            else:
                emotions_count[journal.emotions] = 1
        emotions_unique = sorted(emotions_count, key=emotions_count.get, reverse=True)[
            :5
        ]

        for emotion in emotions_unique:
            stress_counts = {}
            for journal in journals:
                stress_level = journal.stress_level
                if emotion in journal.emotions:
                    if stress_level in stress_counts:
                        stress_counts[stress_level] += 1
                    else:
                        stress_counts[stress_level] = 1
            emotions_stress_counts[emotion] = stress_counts

        stress_values = []
        no_stress_values = []

        for emotion, stress_counts in emotions_stress_counts.items():
            if "Stress" in stress_counts:
                stress_values.append(stress_counts["Stress"])
            else:
                stress_values.append(0 if emotion not in emotions_unique else 0.05)

            if "No Stress" in stress_counts:
                no_stress_values.append(stress_counts["No Stress"])
            else:
                no_stress_values.append(0 if emotion not in emotions_unique else 0.05)

        print(stress_values, no_stress_values)
        print(emotions_stress_counts)

        # Last 12 months emotions count
        last_12_months_emotions = []
        max_occurred_emotions = []
        emotion_counts = []

        current_month = (
            datetime.now(IST).date().replace(day=1)
        )  # Get the first day of the current month

        for i in range(12):
            month_start = current_month - relativedelta(months=i)
            month_end = month_start + relativedelta(
                day=31
            )  # Get the last day of the month
            month_journals = (
                Journal.query.filter_by(user_id=user_id)
                .filter(Journal.date >= month_start, Journal.date <= month_end)
                .all()
            )

            emotions_dict = {}
            for journal in month_journals:
                emotions = Journal.query.filter_by(jid=journal.jid).all()
                for emotion in emotions:
                    if emotion.emotions in emotions_dict:
                        emotions_dict[emotion.emotions] += 1
                    else:
                        emotions_dict[emotion.emotions] = 1

            if emotions_dict:
                max_emotion = max(emotions_dict, key=emotions_dict.get)
                max_count = emotions_dict[max_emotion]

                # Check if there are multiple emotions with the same count
                multiple_emotions = [
                    emotion
                    for emotion, count in emotions_dict.items()
                    if count == max_count
                ]

                if len(multiple_emotions) > 1:
                    # Fetch the emotion with the maximum value from the Emotions dataset
                    max_emotion = max(
                        multiple_emotions,
                        key=lambda emotion: Emotions.query.filter_by(
                            emotion_name=emotion
                        )
                        .first()
                        .value,
                    )

                max_count = emotions_dict[max_emotion]
            else:
                max_emotion = "No Emotion"
                max_count = 0

            last_12_months_emotions.append(month_start.strftime("%B, %Y"))
            max_occurred_emotions.append(max_emotion)
            emotion_counts.append(max_count)

        max_occurred_emotions.reverse()
        emotion_counts.reverse()
        last_12_months_emotions.reverse()
        # print(last_12_months_emotions, max_occurred_emotions, emotion_counts)

        return render_template(
            "analytics.html",
            user=user,
            journals=journals,
            label=label,
            data=data,
            stress_label=stress_label,
            stress_data=stress_data,
            word_counts=word_counts,
            last_month_dates=last_month_dates,
            last_12_months_emotions=last_12_months_emotions,
            max_occurred_emotions=max_occurred_emotions,
            emotion_counts=emotion_counts,
            total_word_count=total_word_count,
            total_entries=total_entries,
            longest_continuous_days=longest_continuous_days,
            continuous_days=continuous_days,
            emotions_unique=emotions_unique,
            stress_values=stress_values,
            no_stress_values=no_stress_values,
        )
    else:
        print("Error")


@app.route("/Wave/<user_id>/profile", methods=["GET", "POST"])
def view_profile(user_id):
    if request.method == "GET":
        user = User.query.filter_by(user_id=user_id).first()
        continuous_days = streak(user_id)
        return render_template(
            "profile.html", user=user, continuous_days=continuous_days
        )
    else:
        return render_template("404_error.html")


@app.route("/Wave/<user_id>/profile/edit", methods=["GET", "POST"])
def edit_profile(user_id):
    if request.method == "GET":
        user = User.query.filter_by(user_id=user_id).first()
        continuous_days = streak(user_id)
        return render_template(
            "profile.html", user=user, continuous_days=continuous_days
        )
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


@app.route("/Wave/<user_id>/mhr")
def mhr(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    continuous_days = streak(user_id)
    print(continuous_days)
    return render_template("mhr.html", user=user, continuous_days=continuous_days)
