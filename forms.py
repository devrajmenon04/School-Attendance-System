from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, DateField, SelectField, PasswordField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class StudentForm(FlaskForm):
    roll = StringField('Roll', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    clazz = StringField('Class', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AttendanceForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Save')