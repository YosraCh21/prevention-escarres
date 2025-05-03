from flask import Flask
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from models import db, Patient, User, Analyse
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from flask_migrate import Migrate
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import imagehash
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from threading import Timer
import smtplib
from email.message import EmailMessage
from werkzeug.security import generate_password_hash
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

load_dotenv()

from keras.models import load_model 
from keras.preprocessing import image 
import numpy as np

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
app.config['MAIL_RESET_PASSWORD_SUBJECT'] = "Réinitialisation de votre mot de passe"
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME') 
mail = Mail(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
DATABASE_FOLDER = 'images_database'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patients.db'  
app.config['UPLOAD_FOLDER'] = 'C:/Users/DELL/Desktop/MonProjet/static/uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
TRESHOLD = 10

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db.init_app(app)
migrate = Migrate(app, db)

from models import Patient, User, Analyse

with app.app_context():
    db.create_all()
model = load_model(r"C:\Users\DELL\Desktop\MonProjet\modele_ulcere.h5", compile=False)

parametres = {
    "corpulence": [
        {"label": "Moyenne", "score": 0},
        {"label": "Au-dessus de la moyenne", "score": 1},
        {"label": "Obèse", "score": 2},
        {"label": "En dessous de la moyenne", "score": 3}
    ],
    "type_peau": [
        {"label": "Saine", "score": 0},
        {"label": "Fine", "score": 1},
        {"label": "Sèche", "score": 1},
        {"label": "Œdémateuse", "score": 1},
        {"label": "Moite/Fièvre", "score": 1},
        {"label": "Décolorée Grade 1", "score": 2},
        {"label": "Lésée/Plaie Grade 2-4", "score": 3}
    ],
    "age": [
        {"label": "14-49", "score": 1},
        {"label": "50-64", "score": 2},
        {"label": "65-74", "score": 3},
        {"label": "75-80", "score": 4},
        {"label": ">81", "score": 5}
    ],
    "continence": [
        {"label": "Complète/Sondé", "score": 0},
        {"label": "Incontinence occasionnelle", "score": 1},
        {"label": "Sondé/Incontinence fécale", "score": 2},
        {"label": "Doublement incontinent", "score": 3}
    ],
    "mobilite": [
        {"label": "Totalement mobile", "score": 0},
        {"label": "Agité/Nerveux", "score": 1},
        {"label": "Apathique", "score": 2},
        {"label": "Restreint", "score": 3},
        {"label": "Alité/Traction", "score": 4},
        {"label": "Confiné au fauteuil", "score": 5}
    ],
    "appetit": [
        {"label": "Normal", "score": 0},
        {"label": "Faible", "score": 1},
        {"label": "Sonde NG/Liquides uniquement", "score": 2},
        {"label": "NPO/Anorexique", "score": 3}
    ],
    "facteurs_risque": {
        "malnutrition": [
            {"label": "aucun", "score": 0},
            {"label": "Cachexie terminale", "score": 8},
            {"label": "Défaillance multi-organes", "score": 8},
            {"label": "Défaillance d'un organe", "score": 5},
            {"label": "Maladie vasculaire périphérique", "score": 5},
            {"label": "Anémie", "score": 2},
            {"label": "Tabagisme", "score": 1}
        ],
        "deficit_neuro": [
            {"label": "aucun", "score": 0},
            {"label": "Diabète/SEP/AVC", "score": 6},
            {"label": "Paralysie motrice/sensorielle", "score": 6}
        ],
        "chirurgie": [
            {"label": "Aucun", "score": 0},
            {"label": "Orthopédique/Rachis", "score": 5},
            {"label": "Sur table >2 hrs", "score": 5}
        ],
        "medication": [
            {"label": "Stéroïdes", "score": 4},
            {"label": "Cytotoxiques", "score": 4},
            {"label": "Anti-inflammatoires", "score": 4},
            {"label": "sans médication", "score": 0}
        ]
    }
}
@app.route('/get_time')
def get_time():
    utc_time = datetime.utcnow()
    manual_correction = utc_time + timedelta(hours=1)
    return jsonify({
        "time": manual_correction.isoformat(),
        "info": "UTC+1 (correction manuelle)"
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name'].strip().capitalize() 
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        if not all([name, email, password]):
            return render_template('login.html', 
                               error="Tous les champs sont obligatoires")

        if len(password) < 8:
            return render_template('login.html',
                               error="Le mot de passe doit contenir au moins 8 caractères")
        
        user = User.query.filter_by(email=email).first()

        if user:
            if check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['name'] = user.name  
                session['email'] = email 
                return redirect(url_for('home'))
            else:
                return render_template('login.html', 
                               error="Mot de passe incorrect")
    
        else:
            hashed_pw = generate_password_hash(
                password,
                method='pbkdf2:sha256',
                salt_length=16
            )
            new_user = User(name=name, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            send_welcome_email(new_user)

            session['user_id'] = new_user.id
            session['email'] = email  
            session['name'] = name

            return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            user = User.query.filter_by(email=email).first()
            
            if user:
                token = user.generate_reset_token()
                send_password_reset_email(user, token)
                return render_template('reset_password_request.html',
                                   success="Un email de réinitialisation a été envoyé")
            
            return render_template('reset_password_request.html',
                               error="Aucun compte associé à cet email")
            
        except Exception as e:
            return render_template('reset_password_request.html',
                               error="Une erreur est survenue lors de l'envoi")
    
    return render_template('reset_password_request.html')

def send_welcome_email(user):
    msg = Message(
        "Bienvenue sur notre plateforme",
        recipients=[user.email],
        body=f"""Bonjour {user.name},
        
Votre compte infirmier a été créé avec succès.
"""
    )
    mail.send(msg)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if User.query.filter_by(email=email).first():
        return render_template('login.html', 
                           error="Cet email est déjà utilisé")
    
    hashed_pw = generate_password_hash(password)
    new_user = User(name=name, email=email, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    
    return redirect(url_for('login', success="Compte créé avec succès"))

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_token(token)
    if not user:
        return render_template('invalid_token.html')
    
    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            return render_template('reset_password.html', 
                               error="Les mots de passe ne correspondent pas",
                               token=token)
        
        if len(new_password) < 8:
            return render_template('reset_password.html',
                               error="Le mot de passe doit contenir au moins 8 caractères",
                               token=token)
        
        has_upper = any(c.isupper() for c in new_password)
        has_lower = any(c.islower() for c in new_password)
        has_digit = any(c.isdigit() for c in new_password)
        has_special = any(not c.isalnum() for c in new_password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            error_msg = """Le mot de passe doit contenir: au moins 8 caractères,une majuscule, une minuscule et un caractère spécial """
            return render_template('reset_password.html',
                               error=error_msg,
                               token=token)
        

        user.password = generate_password_hash(new_password)
        db.session.commit()
        return redirect(url_for('login', success="Mot de passe mis à jour avec succès"))
    
    return render_template('reset_password.html', token=token)

def send_password_reset_email(user, token):
    try:
        msg = Message(
            subject=app.config['MAIL_RESET_PASSWORD_SUBJECT'],
            recipients=[user.email],
            sender=app.config['MAIL_DEFAULT_SENDER'],
            body=f"""Pour réinitialiser votre mot de passe, cliquez sur ce lien :
{url_for('reset_password', token=token, _external=True)}

Ce lien expirera dans 30 minutes.
"""
        )
        mail.send(msg)
    except Exception as e:
        app.logger.error(f"Erreur d'envoi d'email: {str(e)}")
        raise

@app.route('/home')
def home():
    if 'email' not in session:
        return redirect(url_for('login'))
    try:
        user = User.query.filter_by(email=session['email']).first_or_404()
        patients = Patient.query.filter_by(user_id=user.id).order_by(Patient.nom.asc()).all()

        return render_template('index.html',
                            name=user.name,
                            patients=patients)
    
    except Exception as e:
        app.logger.error(f"Erreur accès home : {str(e)}")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('email', None)  
    session.pop('name', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    patients = Patient.query.all()  
    if 'email' not in session:
        return redirect(url_for('login')) 

    return render_template('index.html', parametres=parametres, patients=patients)

@app.route('/nouveau_patient', methods=['GET', 'POST'])
def nouveau_patient():
    if 'user_id' not in session:  
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            nom = request.form.get('nom', '').strip()
            age = request.form.get('age', '').strip()
            chambre = request.form.get('chambre', '').strip()
            lit = request.form.get('lit', '').strip()
            
            if not all([nom, age, chambre, lit]):
                return render_template('nouveau_patient.html', 
                                    error="Tous les champs sont obligatoires",
                                    form_data=request.form)
            if not age.isdigit() or int(age) <= 0:
                return render_template('nouveau_patient.html',
                                    error="L'âge doit être un nombre positif",
                                    form_data=request.form)

            user_id = session.get('user_id')
            patient = Patient(
                nom=nom,
                age=int(age),
                chambre=chambre,
                lit=lit,
                user_id=user_id
            )
            db.session.add(patient)
            db.session.commit() 
            return redirect(url_for('fiche_patient', patient_id=patient.id))
        except Exception as e:
            return render_template('nouveau_patient.html',
                                error="Une erreur technique est survenue",
                                form_data=request.form)

    return render_template('nouveau_patient.html', patient=None)

@app.route('/patient_details/<int:patient_id>')
def patient_details(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    for analyse in patient.analyses:
        analyse.timestamp_adjusted = analyse.timestamp + timedelta(hours=1)
    analyses = Analyse.query.filter_by(patient_id=patient_id).order_by(Analyse.timestamp.desc()).all()

    return render_template('patient_details.html', patient=patient, analyses=analyses)

def predict_image(image_path): 
    """Prédit le stade d'une escarre à partir d'une image"""
    img = image.load_img(image_path, target_size=(128, 128))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)  

    predictions = model.predict(img_array)
    class_index = np.argmax(predictions)
    confidence = predictions[0][class_index] * 100  

    stades = ["Stade 1", "Stade 2", "Stade 3", "Stade 4"]
    
    if confidence < 60:  
        return None, confidence  
    else:
        return stades[class_index], confidence  

def analyser_image(image_path):
    stade, confiance = predict_image(image_path)
    if stade is None:
        return "Aucune lésion d'escarre détectée."
    else:
        return f"Stade prédit: {stade} (Confiance: {confiance:.2f}%)"

@app.route('/nouvelle_analyse/<int:patient_id>', methods=['GET', 'POST'])
def nouvelle_analyse(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    if request.method == 'POST':

        score_waterlow = patient.score_waterlow

        if not score_waterlow or score_waterlow == 0:
            return "Score Waterlow invalide", 400

        resultat_analyse = analyser_image(patient.image_path) 

        nouvelle_analyse = Analyse(
            patient_id=patient.id,
            score_waterlow=score_waterlow or 0,
            resultat=resultat_analyse,
            timestamp=datetime.utcnow()
        )
        db.session.add(nouvelle_analyse)
        db.session.commit()
        
        print("Analyse enregistrée :", nouvelle_analyse.score_waterlow, nouvelle_analyse.resultat)


        return redirect(url_for('patient_details', patient_id=patient.id))

    return render_template('fiche_patient.html', patient=patient)


@app.route('/delete_patient/<int:patient_id>', methods=['POST'])
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    Analyse.query.filter_by(patient_id=patient_id).delete()
    
    db.session.delete(patient)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/fiche_patient/<int:patient_id>')
def fiche_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    analyses = Analyse.query.filter_by(patient_id=patient_id).order_by(Analyse.timestamp.desc()).all()
    return render_template('fiche_patient.html', patient=patient, analyses=analyses)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compare_image(image_path, database_folder):
    try:
        image = Image.open(image_path)
        hash1 = imagehash.average_hash(image)
        best_match = None
        best_distance = float("inf")

        for filename in os.listdir(database_folder):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                img_db = Image.open(os.path.join(database_folder, filename))
                hash2 = imagehash.average_hash(img_db)
                distance = hash1 - hash2
                if distance < best_distance:
                    best_distance = distance
                    best_match = filename

        if best_distance <= TRESHOLD:
            return f"Image reconnue : {best_match} (Différence : {best_distance})"
        else:
            return "Image non reconnue ou qualité insuffisante"

    except Exception as e:
        return f"Erreur lors de la comparaison des images : {e}"

@app.route('/upload/<int:patient_id>', methods=['POST'])
def upload(patient_id):
    try:
        if 'image' not in request.files:
            return jsonify({"message": "Aucune image envoyée"}), 400

        file = request.files['image']
        print("Fichiers reçus :", request.files)  
        if file.filename == '':
            return jsonify({"message": "Nom de fichier vide"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            stade, confiance = predict_image(file_path)

            if stade is None:
                return jsonify({"message": "Image non reconnue ou confiance trop faible."}), 400
            else:
                return jsonify({
                    "message": f"Stade prédit : {stade}",
                    "confiance": f"{confiance:.2f}%",
                    "filename": filename
                })
        else:
            return jsonify({"message": "Format de fichier non autorisé"}), 400

    except Exception as e:
        return jsonify({"message": f"Erreur lors du téléchargement : {str(e)}"}), 500

@app.route('/reconnaissance_image/<int:patient_id>', methods=['POST'])
def reconnaissance_image(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    if 'image' not in request.files:
        return redirect(url_for('fiche_patient', patient_id=patient.id))
    file = request.files['image']
    if file.filename == '':
        return redirect(url_for('fiche_patient', patient_id=patient.id))
    
    if not allowed_file(file.filename):
            return redirect(url_for('fiche_patient', patient_id=patient.id)) 

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        print("Fichiers reçus :", request.files)

        stade, confiance = predict_image(filepath)

        if stade is None:
            resultat = "Aucune lésion d'escarre détectée."
        else:
            resultat = f"Stade prédit: {stade} (Confiance: {confiance:.2f}%)"

        patient.image_path = filepath
        db.session.commit()
        
        nouvelle_analyse = Analyse(
            patient_id=patient.id,
            score_waterlow=patient.score_waterlow,
            resultat=resultat
        )
        db.session.add(nouvelle_analyse)
        db.session.commit()

        return render_template('fiche_patient.html', patient=patient, resultat=resultat, image_filename=filename)
    return redirect(url_for('fiche_patient', patient_id=patient.id))

def check_waterlow_score_and_notify(patient):
    if patient.score_waterlow >= 15 and patient.notifications_enabled:
        email = session.get('email')
        if email:
            Timer(7200.0, send_email_directly, args=[email, patient.nom, patient.score_waterlow]).start()
            print(f"⏳ Notification programmée pour {patient.nom} (dans 2 heures)")

def send_email_directly(to_email, patient_name, score):
    try:
        msg = EmailMessage()
        msg.set_content(f"""
        ALERTE WATERLOW - Score critique
        Patient: {patient_name}
        Score: {score}
        Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """)
        
        msg['Subject'] = '🔴 Alerte Escarre - Intervention Requise'
        msg['From'] = os.getenv('MAIL_USERNAME')
        msg['To'] = to_email

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
            server.send_message(msg)
        
        print(f"✅ Email envoyé à {to_email}")
    except Exception as e:
        print(f"❌ Erreur SMTP: {str(e)}")

def send_delayed_notification(self, email, patient_nom, score_waterlow):
    try:
        if not email:
            raise ValueError("Email recipient not provided")

        msg = Message(
            "Alerte - Risque élevé d'escarres",
            recipients=[email],
            body=f"""
            ALERTE WATERLOW CRITIQUE
            -----------------------
            Patient: {patient_nom}
            Score: {score_waterlow}
            Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            
            Action requise: Intervention immédiate recommandée.
            """
        )
        
        with app.app_context():
            mail.send(msg)
            
        print(f"Notification envoyée à {email}")
        return True
        
    except Exception as exc:
        print(f"Échec d'envoi (tentative {self.request.retries}/{self.max_retries}): {exc}")
        self.retry(exc=exc)

WATERLOW_PARAMS = [
    'corpulence', 'type_peau', 'age', 'continence', 
    'mobilite', 'appetit', 'malnutrition', 
    'deficit_neuro', 'chirurgie', 'medication'
]

@app.route('/waterlow_score/<int:patient_id>', methods=['GET', 'POST'])
def waterlow_score(patient_id):
    if 'email' not in session:
        return redirect(url_for('login'))

    patient = Patient.query.get_or_404(patient_id)
    recommendations = []

    if request.method == 'POST':
        data = request.form
        score_total = 0
        for param in WATERLOW_PARAMS:
            values = request.form.getlist(param)
            for val in values:
                if val.isdigit():
                    score_total += int(val)

        patient.notifications_enabled = 'notifications' in request.form
        patient.score_waterlow = score_total if score_total >=0 else None
        
        nouvelle_analyse = Analyse(
            patient_id=patient.id,
            score_waterlow=patient.score_waterlow,
            resultat='Score calculé',
            timestamp=datetime.utcnow()
        )
        db.session.add(nouvelle_analyse)
        if score_total >= 15:
            check_waterlow_score_and_notify(patient)
            
        db.session.commit()
        db.session.refresh(patient) 

    score_total = patient.score_waterlow if patient.score_waterlow is not None else None

    if score_total is not None:
        if score_total < 10:
            recommendations = [
                "Risque faible : Surveillance régulière.",
                "Maintenir une alimentation équilibrée.",
                "Encourager la mobilité."
            ]
        elif 10 <= score_total <= 14:
            recommendations = [
                "Risque modéré : Vérification fréquente de la peau.",
                "Utilisation d'un matelas en mousse.",
                "Hydratation adéquate."
            ]
        elif 15 <= score_total <= 19:
            check_waterlow_score_and_notify(patient)
            db.session.refresh(patient)
            recommendations = [
                "Risque élevé : Surveillance rapprochée.",
                "Changement de position toutes les 2-3 heures.",
                "Utilisation de coussins de décharge."
            ]
        else:
            check_waterlow_score_and_notify(patient)
            db.session.refresh(patient)
            recommendations = [
                "Risque très élevé : Matelas à air motorisé.",
                "Repositionnement toutes les 2 heures.",
                "Consultation spécialisée recommandée."
            ]

    return render_template('waterlow_score.html', 
                           patient=patient,
                           recommendations=recommendations,
                           notifications_enabled=patient.notifications_enabled)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)