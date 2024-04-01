from sqlalchemy import Column, Date, ForeignKey, Integer, String, Unicode
from sqlalchemy.orm import relationship
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

from app import db

secret_key = b"Sixteen byte key"


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    contact = db.Column(db.String(15))
    emergency_contact = db.Column(db.String(15))
    medical_history = db.Column(db.String(50))
    profile_picture = db.Column(db.String())

    # Add the relationship with Journal
    journals = relationship("Journal", back_populates="user")


class Journal(db.Model):
    jid = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    entry = Column(StringEncryptedType(Unicode, secret_key, AesEngine, "pkcs5"))
    emotions = Column(String(100), nullable=False)
    stress_level = Column(String, nullable=False)
    word_count = Column(Integer, nullable=False)

    # Add the relationship with User
    user = relationship("User", back_populates="journals")
    journal = relationship("Emotions", back_populates="emotion")


class Emotions(db.Model):
    eid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jid = db.Column(db.Integer, ForeignKey("journal.jid"), nullable=False)
    emotion_name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Integer, nullable=False)

    emotion = relationship("Journal", back_populates="journal")
