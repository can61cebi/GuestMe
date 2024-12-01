from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FloatField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    confirm_password = PasswordField('Şifre Tekrar', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Rol', choices=[('user', 'Kullanıcı'), ('host', 'Ev Sahibi')], validators=[DataRequired()])
    submit = SubmitField('Kayıt Ol')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    submit = SubmitField('Giriş Yap')

class PropertyForm(FlaskForm):
    title = StringField('Başlık', validators=[DataRequired()])
    description = TextAreaField('Açıklama', validators=[DataRequired()])
    location = StringField('Adres', validators=[DataRequired()])
    price = FloatField('Fiyat', validators=[DataRequired()])
    latitude = HiddenField('Enlem', validators=[DataRequired()])
    longitude = HiddenField('Boylam', validators=[DataRequired()])
    submit = SubmitField('Evi Ekle')
