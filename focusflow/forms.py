from flask_wtf import FlaskForm
from wtforms import StringField,SelectField, PasswordField, BooleanField, SubmitField, TextAreaField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from wtforms.fields.datetime import DateTimeLocalField
from focusflow.models import Category


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class ResendVerificationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Resend Verification')


class TodoForm(FlaskForm):
    content = StringField('Task Content', validators=[DataRequired()])


    category = SelectField('Category',coerce=int)

    due_date = DateTimeLocalField('Due Date', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    reminder_active = BooleanField('Set Reminder')
    reminder_time = SelectField('Remind me', choices=[
        ('10', '10 minutes before'),
        ('30', '30 minutes before'),
        ('60', '1 hour before'),
        ('120', '2 hours before')
    ], default='30')
    completed = BooleanField('Completed')
    submit = SubmitField('Add Task')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categories = Category.query.order_by(Category.name).all()
        self.category.choices = [(0, 'Select a category...')] + [(c.id, c.name) for c in categories]



