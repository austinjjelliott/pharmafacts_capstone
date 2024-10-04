from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Length, Email


class UserForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(max=20)])
    password = PasswordField("Password", validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email(), Length(max=50)])
    first_name = StringField('First Name', validators=[InputRequired(), Length(max = 30)])
    last_name = StringField('Last Name', validators=[InputRequired(), Length(max = 30)])


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(max=20)])
    password = PasswordField("Password", validators=[InputRequired()])

class EditUserForm(FlaskForm):
    username = StringField("Username", validators=[ Length(max=20)])
    email = StringField('Email', validators=[Email(), Length(max=50)])
    first_name = StringField('First Name', validators=[Length(max = 30)])
    last_name = StringField('Last Name', validators=[Length(max = 30)])
    password = PasswordField("Password", validators=[])

