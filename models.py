# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date, timedelta

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'host'

    properties = db.relationship('Property', backref='host', lazy=True)

class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)  # Enlem
    longitude = db.Column(db.Float, nullable=False) # Boylam

    reservations = db.relationship('Reservation', backref='property', lazy=True, cascade="all, delete-orphan")
    availabilities = db.relationship('Availability', backref='property', lazy=True, cascade="all, delete-orphan")

    def has_future_availability(self):
        # has_future_availability basitçe get_marker_color == green'e bakıyor.
        return self.get_marker_color() == "green"

    def get_marker_color(self):
        future_avails = [av for av in self.availabilities if av.end_date >= date.today()]
        if not future_avails:
            # Geleceğe dönük hiç müsaitlik yoksa ev tamamen dolu kabul,
            # mantık gereği bu durumda boş gün de yok => red
            return "red"

        # Rezervasyonları durumlarına göre ayır
        pending_intervals = [(r.start_date, r.end_date) for r in self.reservations if r.status == 'pending']
        approved_intervals = [(r.start_date, r.end_date) for r in self.reservations if r.status == 'approved']

        def day_reserved_status(d):
            p = any(ps <= d <= pe for (ps, pe) in pending_intervals)
            a = any(as_ <= d <= ae for (as_, ae) in approved_intervals)
            return p, a

        free_days = 0
        pending_days = 0
        approved_days = 0

        # Tüm future_avails günlerini kontrol ediyoruz
        for av in future_avails:
            current_day = av.start_date
            while current_day <= av.end_date:
                # Bu günün durumunu kontrol et
                p, a = day_reserved_status(current_day)

                if not p and not a:
                    # Gün serbest
                    free_days += 1
                elif p and not a:
                    # Gün pending rezervasyonla dolu
                    pending_days += 1
                elif a and not p:
                    # Gün approved rezervasyonla dolu
                    approved_days += 1
                else:
                    # Hem pending hem approved olma ihtimali çok düşük,
                    # ama yine de pending öncelikli sayıyoruz (ya da karışık durum sarıya gidecek)
                    pending_days += 1
                current_day += timedelta(days=1)

        # Renk belirleme:
        if free_days > 0:
            return "green"
        # Boş gün yok
        if pending_days > 0 and approved_days == 0:
            return "yellow"
        elif approved_days > 0 and pending_days == 0:
            return "red"
        else:
            # Karışık durum (hem pending hem approved) => yellow
            return "yellow"


    def is_date_range_available(self, start_date, end_date):
        in_availability = False
        for av in self.availabilities:
            if start_date >= av.start_date and end_date <= av.end_date:
                in_availability = True
                break
        if not in_availability:
            return False

        for r in self.reservations:
            if r.status in ['pending', 'approved']:
                if not (end_date < r.start_date or start_date > r.end_date):
                    return False
        return True


class Availability(db.Model):
    __tablename__ = 'availability'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)


class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(10), nullable=False)  # 'pending', 'approved', 'rejected', 'canceled'
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    cancel_reason = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref='reservations')
