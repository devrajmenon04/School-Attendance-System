from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import csv
import io


from models import db, User, Student, Attendance
from forms import LoginForm, StudentForm, AttendanceForm
import config


app = Flask(__name__)
app.config.from_object(config)


db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


setup_done = False

@app.before_request
def create_tables():
    global setup_done
    if not setup_done:
        db.create_all()
        # create default admin if not exists
        if not User.query.filter_by(username='admin').first():
            pw = generate_password_hash('admin', method='pbkdf2:sha256')
            u = User(username='admin', password=pw)
            db.session.add(u)
            db.session.commit()
        setup_done = True


@app.route('/')
@login_required
def index():
    total_students = Student.query.count()
    today = date.today()
    today_att = Attendance.query.filter_by(date=today).count()
    return render_template('index.html', total_students=total_students, today_att=today_att)


@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/students')
@login_required
def students():
    students = Student.query.order_by(Student.roll).all()
    attendance_percentages = {
        student.id: get_attendance_percentage(student.id)
        for student in students
    }
    return render_template('students.html', students=students, attendance_percentages=attendance_percentages)


@app.route('/students/add', methods=['GET','POST'])
@login_required
def add_student():
    form = StudentForm()
    if form.validate_on_submit():
        s = Student(roll=form.roll.data, name=form.name.data, clazz=form.clazz.data)  
        db.session.add(s)
        db.session.commit()
        flash('Student added')
        return redirect(url_for('students'))
    return render_template('add_student.html', form=form)  


@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    form = StudentForm(obj=student)
    if form.validate_on_submit():
        student.roll = form.roll.data
        student.name = form.name.data
        student.clazz = form.clazz.data
        # Removed notes
        db.session.commit()
        flash('Student updated successfully!')
        return redirect(url_for('students'))
    return render_template('student_form.html', form=form, title="Edit Student")


@app.route('/students/delete/<int:student_id>', methods=['POST', 'GET'])
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully!')
    return redirect(url_for('students'))


@app.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    form = AttendanceForm()
    students = Student.query.order_by(Student.roll).all()
    today = date.today()
    attendance_dict = {}

    # Load today's attendance if exists
    if request.method == 'GET':
        records = Attendance.query.filter_by(date=today).all()
        attendance_dict = {record.student_id: record.present for record in records}

    if form.validate_on_submit():
        att_date = form.date.data
        # Remove existing attendance for the date
        Attendance.query.filter_by(date=att_date).delete()
        for student in students:
            present = f'present_{student.id}' in request.form
            record = Attendance(student_id=student.id, date=att_date, present=present)
            db.session.add(record)
        db.session.commit()
        flash('Attendance marked!')
        return redirect(url_for('attendance'))

    # For GET, pre-fill form date with today
    if request.method == 'GET' and not form.date.data:
        form.date.data = today

    return render_template(
        'attendance.html',
        form=form,
        students=students,
        attendance=[sid for sid, present in attendance_dict.items() if present]
    )

from datetime import datetime

@app.route('/report', methods=['GET'])
@login_required
def report():
    date_str = request.args.get('date')
    records = []
    present_count = 0
    absent_count = 0
    filter_date = None

    if date_str:
        try:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            records = Attendance.query.filter_by(date=filter_date).all()
            present_count = Attendance.query.filter_by(date=filter_date, present=True).count()
            absent_count = Attendance.query.filter_by(date=filter_date, present=False).count()
        except ValueError:
            records = []
    else:
        # Show all records if no date is selected (optional)
        records = Attendance.query.order_by(Attendance.date.desc()).all()

    return render_template(
        'report.html',
        records=records,
        present_count=present_count,
        absent_count=absent_count,
        filter_date=filter_date
    )

def get_attendance_percentage(student_id, total_days=200):
    present_days = Attendance.query.filter_by(student_id=student_id, present=True).count()
    percentage = (present_days / total_days) * 100 if total_days > 0 else 0
    return round(percentage, 2)

if __name__ == '__main__':
    app.run(debug=True)