from extensions import db
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer
import pytz

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    chambre = db.Column(db.String(50), nullable=False)
    lit = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    image_path = db.Column(db.String(200), nullable=True)
    score_waterlow = db.Column(db.Integer, nullable=True)
    resultat = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  
    notifications_enabled = db.Column(db.Boolean, default=False)
    analyses = db.relationship('Analyse', back_populates='patient', cascade='all, delete')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', back_populates='patients')


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    patients = db.relationship('Patient', back_populates='user', cascade='all, delete-orphan')
    
    def generate_reset_token(self, expires_sec=1800):
        from flask import current_app  
        s = URLSafeTimedSerializer(
            current_app.config['SECRET_KEY'],
            salt='password-reset'
        )
        return s.dumps({'user_id': self.id})  

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        from flask import current_app
        s = URLSafeTimedSerializer(
            current_app.config['SECRET_KEY'],
            salt='password-reset'
        )
        try:
            data = s.loads(token, max_age=1800)
            return User.query.get(data['user_id'])
        except:
            return None
class Analyse(db.Model):
    __tablename__ = 'analyses'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    score_waterlow = db.Column(db.Integer, nullable=True)
    resultat = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('Patient', back_populates='analyses')
    @property
    def timestamp_adjusted(self):
        """Convertit le timestamp UTC en heure locale"""
        utc_time = self.timestamp.replace(tzinfo=pytz.utc)
        local_time = utc_time.astimezone(pytz.timezone('Europe/Paris'))  
        return local_time