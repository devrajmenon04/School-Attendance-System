from datetime import date
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(200), nullable=False)  # store hashed password in production


class Student(db.Model):
    id = Column(Integer, primary_key=True)
    roll = Column(String(20), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    clazz = Column(String(50))
    attendances = relationship('Attendance', back_populates='student', cascade='all, delete-orphan')


class Attendance(db.Model):
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('student.id'), nullable=False)
    date = Column(Date, nullable=False)
    present = Column(Boolean, default=True)
    student = relationship('Student', back_populates='attendances')


__table_args__ = (db.UniqueConstraint('student_id', 'date', name='uix_student_date'),)