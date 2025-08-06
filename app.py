
from flask import Flask, request, render_template, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime
import csv
from io import StringIO
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecret")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Implique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    nationalite = db.Column(db.String(100))
    date_naissance = db.Column(db.String(20))
    blesse = db.Column(db.String(10))
    reloges = db.Column(db.String(10))
    animaux = db.Column(db.String(10))
    effets_perso = db.Column(db.Text)
    autres_infos = db.Column(db.Text)
    date_entree = db.Column(db.DateTime, default=datetime.utcnow)
    date_sortie = db.Column(db.DateTime, nullable=True)

USERS = {
    os.environ.get("ENTREE_USER", "entree"): os.environ.get("ENTREE_PASS", "entreepass"),
    os.environ.get("SORTIE_USER", "sortie"): os.environ.get("SORTIE_PASS", "sortiepass"),
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        password = request.form['password']
        if user in USERS and USERS[user] == password:
            session['user'] = user
            return redirect(url_for('dashboard'))
        flash("Identifiants incorrects")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    impliques = Implique.query.order_by(Implique.date_entree.desc()).all()
    total = len(impliques)
    restants = len([i for i in impliques if i.date_sortie is None])
    return render_template('dashboard.html', impliques=impliques, total=total, restants=restants)

@app.route('/entree', methods=['GET', 'POST'])
@login_required
def entree():
    if session.get('user') != 'entree':
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        new = Implique(
            nom=request.form.get('nom'),
            prenom=request.form.get('prenom'),
            nationalite=request.form.get('nationalite'),
            date_naissance=request.form.get('date_naissance'),
            blesse=request.form.get('blesse'),
            reloges=request.form.get('reloges'),
            animaux=request.form.get('animaux'),
            effets_perso=request.form.get('effets_perso'),
            autres_infos=request.form.get('autres_infos')
        )
        db.session.add(new)
        db.session.commit()
        flash("Entrée enregistrée")
        return redirect(url_for('dashboard'))
    return render_template('entree.html')

@app.route('/sortie/<int:id>', methods=['POST'])
@login_required
def sortie(id):
    if session.get('user') != 'sortie':
        return redirect(url_for('dashboard'))
    implique = Implique.query.get_or_404(id)
    implique.date_sortie = datetime.utcnow()
    db.session.commit()
    flash("Sortie enregistrée")
    return redirect(url_for('dashboard'))

@app.route('/export')
@login_required
def export():
    impliques = Implique.query.all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nom', 'Prénom', 'Nationalité', 'Naissance', 'Blessé', 'Relogés', 'Animaux', 'Effets Perso', 'Autres', 'Entrée', 'Sortie'])
    for v in impliques:
        writer.writerow([
            v.id, v.nom, v.prenom, v.nationalite, v.date_naissance, v.blesse,
            v.reloges, v.animaux, v.effets_perso, v.autres_infos,
            v.date_entree.strftime("%Y-%m-%d %H:%M:%S"),
            v.date_sortie.strftime("%Y-%m-%d %H:%M:%S") if v.date_sortie else ''
        ])
    output.seek(0)
    return send_file(output, mimetype='text/csv', download_name='impliques.csv', as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
