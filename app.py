import os
from dotenv import load_dotenv

# Ortam değişkenlerini yükleyelim
load_dotenv('.env')

from flask import Flask, render_template, redirect, url_for, flash
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Property, Reservation
from forms import RegistrationForm, LoginForm, PropertyForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config.from_object(Config)

print(f"SECRET_KEY: {app.config['SECRET_KEY']}")
print(f"DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"GOOGLE_MAPS_API_KEY: {app.config['GOOGLE_MAPS_API_KEY']}")

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Giriş yapılmamışsa yönlendirilecek sayfa

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    properties = Property.query.all()
    return render_template('index.html', properties=properties)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Şifreyi hashleyelim
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        # Yeni kullanıcıyı oluşturalım
        new_user = User(username=form.username.data, email=form.email.data,
                        password=hashed_password, role=form.role.data)
        # Veritabanına ekleyelim
        db.session.add(new_user)
        db.session.commit()
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Kullanıcıyı email ile bulalım
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            # Giriş başarılı
            login_user(user)
            flash('Giriş başarılı!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email veya şifre hatalı.', 'danger')
    return render_template('login.html', form=form)

@app.route('/add_property', methods=['GET', 'POST'])
@login_required
def add_property():
    if current_user.role != 'host':
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('index'))
    form = PropertyForm()
    if form.validate_on_submit():
        # Ev ekleme işlemleri
        new_property = Property(
            host_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            price=form.price.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data
        )
        db.session.add(new_property)
        db.session.commit()
        flash('Ev başarıyla eklendi.', 'success')
        return redirect(url_for('index'))
    google_maps_api_key = app.config['GOOGLE_MAPS_API_KEY']
    return render_template('add_property.html', form=form, google_maps_api_key=google_maps_api_key)

@app.route('/map')
def map_view():
    properties = Property.query.all()
    google_maps_api_key = app.config['GOOGLE_MAPS_API_KEY']
    return render_template('map.html', properties=properties, google_maps_api_key=google_maps_api_key)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('index'))

@app.route('/property/<int:property_id>')
def property_detail(property_id):
    property = Property.query.get_or_404(property_id)
    google_maps_api_key = app.config['GOOGLE_MAPS_API_KEY']
    return render_template('property_detail.html', property=property, google_maps_api_key=google_maps_api_key)

if __name__ == '__main__':
    app.run(debug=True)
