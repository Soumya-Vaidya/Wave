from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from app import db


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    phone_number = db.Column(db.String(15))
    emergency_contact = db.Column(db.String(15))
    medical_history = db.Column(db.String(50))

    # Add the relationship with Journal
    journals = relationship("Journal", back_populates="user")


class Journal(db.Model):
    jid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, ForeignKey("user.user_id"), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    entry = db.Column(db.String(500), nullable=False)
    emotions = db.Column(db.String(100), nullable=False)
    stress_level = db.Column(db.String, nullable=False)
    word_count = db.Column(db.Integer, nullable=False)

    # Add the relationship with User
    user = relationship("User", back_populates="journals")
