from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .models import db, Utilisateur, Evenement
from werkzeug.security import check_password_hash

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("main.login"))
    return redirect(url_for("main.select_role"))

@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Utilisateur.query.filter_by(nom_utilisateur=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect(url_for("main.select_role"))
        else:
            flash("Identifiants invalides")
    return render_template("login.html")

@main_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))

@main_bp.route("/select-role")
def select_role():
    if "user_id" not in session:
        return redirect(url_for("main.login"))
    return render_template("select_role.html")
