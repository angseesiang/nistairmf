from datetime import datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///nist_ai_rmf.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # admin or user
    is_active_account = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.is_active_account


class PromptLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    mapped_category = db.Column(db.String(80), nullable=False)
    status_update = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Admin access required.", "error")
            return redirect(url_for("dashboard"))
        return view_func(*args, **kwargs)

    return wrapper


def map_prompt_to_nist(prompt: str):
    text = prompt.lower()
    if any(k in text for k in ["policy", "governance", "ownership", "oversight"]):
        return "GOVERN"
    if any(k in text for k in ["profile", "inventory", "impact", "context", "risk"]):
        return "MAP"
    if any(k in text for k in ["test", "measure", "monitor", "audit", "validation"]):
        return "MEASURE"
    if any(k in text for k in ["mitigate", "response", "remediate", "control", "action"]):
        return "MANAGE"
    return "UNMAPPED"


@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash("Invalid username or password.", "error")
            return render_template("login.html")
        if not user.is_active_account:
            flash("Account is disabled. Contact an admin.", "error")
            return render_template("login.html")
        login_user(user)
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    logs = PromptLog.query.filter_by(user_id=current_user.id).order_by(PromptLog.created_at.desc()).all()
    return render_template("dashboard.html", logs=logs)


@app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_users.html", users=users)


@app.route("/admin/users/create", methods=["POST"])
@login_required
@admin_required
def admin_create_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "user")

    if not username or not password or role not in {"admin", "user"}:
        flash("Invalid input.", "error")
        return redirect(url_for("admin_users"))

    if User.query.filter_by(username=username).first():
        flash("Username already exists.", "error")
        return redirect(url_for("admin_users"))

    new_user = User(username=username, role=role, is_active_account=True)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    flash("Account created successfully.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/edit", methods=["POST"])
@login_required
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    user.username = request.form.get("username", user.username).strip() or user.username
    role = request.form.get("role", user.role)
    if role in {"admin", "user"}:
        user.role = role

    password = request.form.get("password", "").strip()
    if password:
        user.set_password(password)

    db.session.commit()
    flash("Account updated.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/disable", methods=["POST"])
@login_required
@admin_required
def admin_disable_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot disable your own account.", "error")
    else:
        user.is_active_account = False
        db.session.commit()
        flash("Account disabled.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/enable", methods=["POST"])
@login_required
@admin_required
def admin_enable_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active_account = True
    db.session.commit()
    flash("Account enabled.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "error")
    else:
        db.session.delete(user)
        db.session.commit()
        flash("Account deleted.", "success")
    return redirect(url_for("admin_users"))


@app.route("/chat", methods=["POST"])
@login_required
def chat_update():
    prompt = request.form.get("prompt", "").strip()
    if not prompt:
        flash("Prompt cannot be empty.", "error")
        return redirect(url_for("dashboard"))

    category = map_prompt_to_nist(prompt)
    status_update = f"Mapped to NIST AI RMF function: {category}"

    log = PromptLog(
        user_id=current_user.id,
        prompt=prompt,
        mapped_category=category,
        status_update=status_update,
    )
    db.session.add(log)
    db.session.commit()

    flash(status_update, "success")
    return redirect(url_for("dashboard"))


def initialize_database():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", role="admin", is_active_account=True)
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run(debug=True)

