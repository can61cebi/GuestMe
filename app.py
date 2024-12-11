# app.py

import os
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv('.env')

from flask import Flask, render_template, redirect, url_for, flash, request
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Property, Reservation, Availability
from forms import RegistrationForm, LoginForm, PropertyForm, AvailabilityForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    properties = Property.query.all()
    # Müsaitlik durumunu kontrol edelim
    # Eğer geleceğe dönük en az bir Availability varsa ev müsait (green), yoksa unavailable (yellow).
    for p in properties:
        p.is_available = p.has_future_availability()

    google_maps_api_key = app.config['GOOGLE_MAPS_API_KEY']
    return render_template('index.html', properties=properties, google_maps_api_key=google_maps_api_key)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, email=form.email.data,
                        password=hashed_password, role=form.role.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Giriş başarılı!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email veya şifre hatalı.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('index'))

@app.route('/add_property', methods=['GET', 'POST'])
@login_required
def add_property():
    if current_user.role != 'host':
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('index'))
    form = PropertyForm()
    if form.validate_on_submit():
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
        flash('Ev başarıyla eklendi. Şimdi müsaitlik tarihlerini ekleyebilirsiniz.', 'success')
        return redirect(url_for('manage_property_availability', property_id=new_property.id))
    google_maps_api_key = app.config['GOOGLE_MAPS_API_KEY']
    return render_template('add_property.html', form=form, google_maps_api_key=google_maps_api_key)

@app.route('/property/<int:property_id>')
def property_detail(property_id):
    property = Property.query.get_or_404(property_id)
    google_maps_api_key = app.config['GOOGLE_MAPS_API_KEY']

    availabilities = [
        {
            'start': av.start_date.strftime('%Y-%m-%d'),
            'end': av.end_date.strftime('%Y-%m-%d')
        } for av in property.availabilities
    ]

    # Pending/approved rezervasyonları da alalım
    reserved_ranges = [
        {
            'start': r.start_date.strftime('%Y-%m-%d'),
            'end': r.end_date.strftime('%Y-%m-%d')
        } for r in property.reservations if r.status in ['pending', 'approved']
    ]

    return render_template('property_detail.html',
                           property=property,
                           google_maps_api_key=google_maps_api_key,
                           availabilities=availabilities,
                           reserved_ranges=reserved_ranges)

@app.route('/book_property/<int:property_id>', methods=['POST'])
@login_required
def book_property(property_id):
    property = Property.query.get_or_404(property_id)
    # formdan seçilen tarihi alacağız (tek tarih ya da aralık). Burada basitçe start_date, end_date alıyoruz.
    start_str = request.form.get('start_date')
    end_str = request.form.get('end_date')
    if not start_str or not end_str:
        flash('Lütfen geçerli bir tarih aralığı seçin.', 'danger')
        return redirect(url_for('property_detail', property_id=property_id))
    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Tarih formatı hatalı.', 'danger')
        return redirect(url_for('property_detail', property_id=property_id))

    # Seçilen tarihler müsait mi?
    if not property.is_date_range_available(start_date, end_date):
        flash('Seçtiğiniz tarihlerde bu ev müsait değil.', 'danger')
        return redirect(url_for('property_detail', property_id=property_id))

    # Müsait, rezervasyon oluştur
    new_res = Reservation(property_id=property.id, user_id=current_user.id, date=datetime.now(), status='pending')
    new_res.start_date = start_date
    new_res.end_date = end_date
    db.session.add(new_res)
    db.session.commit()
    flash('Rezervasyon talebiniz oluşturuldu! Host onayından sonra kesinleşecektir.', 'success')
    return redirect(url_for('my_rentals'))

@app.route('/my_rentals')
@login_required
def my_rentals():
    # Kullanıcının yaptığı rezervasyonlar
    reservations = Reservation.query.filter_by(user_id=current_user.id).all()
    return render_template('my_rentals.html', reservations=reservations)

@app.route('/cancel_reservation/<int:reservation_id>', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    res = Reservation.query.get_or_404(reservation_id)
    if res.user_id != current_user.id:
        flash('Bu rezervasyonu iptal etme yetkiniz yok.', 'danger')
        return redirect(url_for('my_rentals'))
    res.status = 'canceled'
    res.cancel_reason = 'Kullanıcı tarafından iptal edildi.'
    db.session.commit()
    flash('Rezervasyon başarıyla iptal edildi.', 'success')
    return redirect(url_for('my_rentals'))

@app.route('/map')
def map_view():
    properties = Property.query.all()
    # Her evin müsaitlik durumunu belirle
    for p in properties:
        p.is_available = p.has_future_availability()
    google_maps_api_key = app.config['GOOGLE_MAPS_API_KEY']
    return render_template('map.html', properties=properties, google_maps_api_key=google_maps_api_key)

@app.route('/manage_properties')
@login_required
def manage_properties():
    if current_user.role != 'host':
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('index'))
    # Host'un sahip olduğu evleri listeler
    properties = Property.query.filter_by(host_id=current_user.id).all()
    return render_template('manage_properties.html', properties=properties)

@app.route('/manage_property_availability/<int:property_id>', methods=['GET', 'POST'])
@login_required
def manage_property_availability(property_id):
    if current_user.role != 'host':
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('index'))
    property = Property.query.get_or_404(property_id)
    if property.host_id != current_user.id:
        flash('Bu ev üzerinde işlem yapma yetkiniz yok.', 'danger')
        return redirect(url_for('manage_properties'))

    form = AvailabilityForm()
    if form.validate_on_submit():
        # Mevcut tüm Availability kayıtlarını önce temizleyelim ya da güncelleyelim
        # Burada basit yaklaşımla önce tüm kayıtları silip sonra yeni aralıklar ekliyoruz
        # Gerçek senaryoda daha sofistike bir yaklaşım gerekebilir.
        Availability.query.filter_by(property_id=property.id).delete()

        # formdan gelecek format: start_date ve end_date birden fazla set olarak
        # Örneğin kullanıcı birden fazla aralık seçmiş olabilir. Burada varsayıyoruz ki kullanıcı tek aralık giriyor.
        # İsterseniz burada daha gelişmiş bir mantık kurabilirsiniz.
        # Şimdilik tek bir aralık ekleyelim.
        start_date = form.start_date.data
        end_date = form.end_date.data
        if start_date and end_date and start_date <= end_date:
            new_av = Availability(property_id=property.id, start_date=start_date, end_date=end_date)
            db.session.add(new_av)
            db.session.commit()

            # Host tarihleri değiştirdiği için bu evin rezervasyonlarını kontrol edip iptal etmeliyiz
            cancel_conflicting_reservations(property)

            flash('Müsaitlik aralıkları güncellendi.', 'success')
            return redirect(url_for('manage_properties'))
        else:
            flash('Geçersiz tarih aralığı.', 'danger')

    # Mevcut müsaitlikleri getir.
    availabilities = property.availabilities
    return render_template('manage_property_availability.html', property=property, form=form, availabilities=availabilities)

def cancel_conflicting_reservations(property):
    # Evdeki rezervasyonları al
    # Yeni müsaitlik durumuna göre uygun olmayan rezervasyonları iptal et
    # Burada basitçe: Evdeki tüm rezervasyonları inceleriz,
    # eğer rezervasyonun tarih aralığı host'un yeni availability ayarına uymuyorsa iptal ederiz.
    # Not: Burada aslında host'un verdiği availability aralıklarını bir union şeklinde değerlendirmek gerekebilir.
    # Basitlik adına tek aralık üzerinden çalıştık. Gelişmiş versiyonda birden çok aralık tutulup
    # rezervasyon tarihinin bu aralıklardan herhangi biri içinde kalıp kalmadığı incelenir.
    # Şimdilik tek aralık varsayıyoruz.

    # Evdeki müsaitlik aralıklarını alalım.
    avails = property.availabilities

    # Eğer hiç availability yoksa tüm rezervasyonlar iptal edilmeli.
    if not avails:
        res_list = Reservation.query.filter_by(property_id=property.id).filter(Reservation.status.in_(['pending', 'approved'])).all()
        for r in res_list:
            r.status = 'canceled'
            r.cancel_reason = 'Host evin müsaitlik ayarlarını değiştirdiği için rezervasyon iptal edildi.'
        db.session.commit()
        return

    # Şimdilik tek aralık varsayımı:
    # Eğer birden fazla aralık varsa, rezervasyonun en az bir aralık içinde kalıp kalmadığına bakarız.
    # Kolaylık için bu kodu da çoklu aralık destekleyecek hale getirelim.
    def in_any_avail(res_start, res_end):
        for av in avails:
            # Eğer rezervasyonun tarihlerinin herhangi bir kısmı av.start_date - av.end_date arasında ise kabul ediyoruz.
            # Kiralamada genelde tam overlapp bakılmalı:
            if not (res_end < av.start_date or res_start > av.end_date):
                return True
        return False

    res_list = Reservation.query.filter_by(property_id=property.id).filter(Reservation.status.in_(['pending', 'approved'])).all()
    for r in res_list:
        # Eğer rezervasyonun tarihleri yeni availability set'ine uymuyorsa iptal et
        if not in_any_avail(r.start_date, r.end_date):
            r.status = 'canceled'
            r.cancel_reason = 'Kiralamak istediğiniz evin özellikleri değiştirildiği için kiralamanız iptal edildi.'
    db.session.commit()

@app.route('/my_rentals_host')
@login_required
def my_rentals_host():
    if current_user.role != 'host':
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('index'))
    # Host'un evlerine yapılan rezervasyonları görmesi
    # Host onay/red işlemi burada yapılabilir.
    properties = Property.query.filter_by(host_id=current_user.id).all()
    # Tüm rezervasyonları çekelim:
    all_res = []
    for p in properties:
        for r in p.reservations:
            all_res.append(r)
    return render_template('my_rentals_host.html', reservations=all_res)

@app.route('/approve_reservation/<int:reservation_id>', methods=['POST'])
@login_required
def approve_reservation(reservation_id):
    if current_user.role != 'host':
        flash('Bu işleme izniniz yok.', 'danger')
        return redirect(url_for('index'))
    res = Reservation.query.get_or_404(reservation_id)
    # Bu rezervasyon ilgili hosta mı ait?
    if res.property.host_id != current_user.id:
        flash('Bu rezervasyonu onaylama yetkiniz yok.', 'danger')
        return redirect(url_for('my_rentals_host'))
    res.status = 'approved'
    db.session.commit()
    flash('Rezervasyon onaylandı.', 'success')
    return redirect(url_for('my_rentals_host'))

@app.route('/reject_reservation/<int:reservation_id>', methods=['POST'])
@login_required
def reject_reservation(reservation_id):
    if current_user.role != 'host':
        flash('Bu işleme izniniz yok.', 'danger')
        return redirect(url_for('index'))
    res = Reservation.query.get_or_404(reservation_id)
    if res.property.host_id != current_user.id:
        flash('Bu rezervasyonu reddetme yetkiniz yok.', 'danger')
        return redirect(url_for('my_rentals_host'))
    res.status = 'rejected'
    db.session.commit()
    flash('Rezervasyon reddedildi.', 'success')
    return redirect(url_for('my_rentals_host'))

if __name__ == '__main__':
    app.run(debug=True)
