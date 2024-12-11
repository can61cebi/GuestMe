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

    # İlişkiler
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
    longitude = db.Column(db.Float, nullable=False)  # Boylam

    reservations = db.relationship('Reservation', backref='property', lazy=True, cascade="all, delete-orphan")
    availabilities = db.relationship('Availability', backref='property', lazy=True, cascade="all, delete-orphan")

    def has_future_availability(self):
        # Bu fonksiyon artık sadece renk belirlemek için değil,
        # önceki mantığı değil de alt tarafta vereceğimiz get_marker_color fonksiyonunu kullanacağız.
        # Burada True/False dönüyordu, ancak yeni mantık için ayrı bir fonksiyon kullanacağız.

        # Eski mantığı korumak isterseniz ya da ihtiyaç duyarsanız kullanabilirsiniz.
        return self.get_marker_color() == "green"

    def get_marker_color(self):
        # Bugünden sonraki müsaitlikleri al
        future_avails = [av for av in self.availabilities if av.end_date >= date.today()]
        if not future_avails:
            # Gelecekte hiç müsaitlik yoksa ev aslında tamamen dolu, bu durumda hepsi approved kabul edilebilir.
            # Ama talimatta böyle bir durum yok. Varsayılan olarak kırmızı diyebilirsiniz.
            return "red"

        earliest_start = min(av.start_date for av in future_avails)

        # Rezervasyonları durumlarına göre ayır
        pending_intervals = [(r.start_date, r.end_date) for r in self.reservations if r.status == 'pending']
        approved_intervals = [(r.start_date, r.end_date) for r in self.reservations if r.status == 'approved']

        def is_day_pending(d):
            for (ps, pe) in pending_intervals:
                if ps <= d <= pe:
                    return True
            return False

        def is_day_approved(d):
            for (as_, ae) in approved_intervals:
                if as_ <= d <= ae:
                    return True
            return False

        free_days = 0
        pending_days = 0
        approved_days = 0

        # İlk gün hariç tüm günleri kontrol et
        for av in future_avails:
            current_day = av.start_date
            while current_day <= av.end_date:
                if current_day > earliest_start:
                    # Bu gün rezervasyon durumunu kontrol et
                    day_pending = is_day_pending(current_day)
                    day_approved = is_day_approved(current_day)

                    if not day_pending and not day_approved:
                        # Bu gün serbest
                        free_days += 1
                    elif day_pending and not day_approved:
                        # Sadece pending
                        pending_days += 1
                    elif day_approved and not day_pending:
                        # Sadece approved
                        approved_days += 1
                    else:
                        # Gün hem pending hem approved olması normalde mümkün değil,
                        # ancak karışık durum için varsayalım ki pending önceliklidir
                        pending_days += 1
                current_day += timedelta(days=1)

        # Renk belirleme:
        # Önce serbest gün var mı bakarız:
        if free_days > 0:
            return "green"  # En az bir serbest gün var => yeşil

        # Serbest gün yoksa ya hepsi pending ya hepsi approved ya da karışık
        if pending_days > 0 and approved_days == 0:
            # Tüm rezervasyonlu günler pending => sarı
            return "yellow"
        elif approved_days > 0 and pending_days == 0:
            # Tüm rezervasyonlu günler approved => kırmızı
            return "red"
        else:
            # Karışık durum (hem pending hem approved günler var)
            # Burada mantık net değil, varsayım: hâlâ tam onaylanmadığı için sarı
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
