from __future__ import annotations
import os
from datetime import timedelta

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-please")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "menu.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.permanent_session_lifetime = timedelta(days=7)

db = SQLAlchemy(app)


class Menu(db.Model):
    __tablename__ = "menus"
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    title_ru = db.Column(db.String(200), nullable=False)
    title_kz = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(500), default="")

    categories = db.relationship("Category", backref="menu_obj", lazy=True, cascade="all, delete")


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    menu_id = db.Column(db.Integer, db.ForeignKey("menus.id"), nullable=False)

    slug = db.Column(db.String(64), unique=True, nullable=False)
    name_ru = db.Column(db.String(200), nullable=False)
    name_kz = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200), nullable=False)

    dishes = db.relationship("Dish", backref="category_obj", lazy=True, cascade="all, delete")


class Dish(db.Model):
    __tablename__ = "dishes"
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    slug = db.Column(db.String(128), unique=True, nullable=False)

    title_ru = db.Column(db.String(200), nullable=False)
    title_kz = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)

    price = db.Column(db.Integer, nullable=False, default=0)

    ing_ru = db.Column(db.Text, default="")
    ing_kz = db.Column(db.Text, default="")
    ing_en = db.Column(db.Text, default="")

    image = db.Column(db.String(500), default="")


class Settings(db.Model):
    __tablename__ = "settings"
    id = db.Column(db.Integer, primary_key=True)

    phone = db.Column(db.String(64), default="")

    bg = db.Column(db.String(64), default="#121015")
    card = db.Column(db.String(64), default="#181820")
    muted = db.Column(db.String(64), default="#9aa3b2")
    text = db.Column(db.String(64), default="#f5f7fb")
    brand = db.Column(db.String(64), default="#ffbd2f")
    accent = db.Column(db.String(64), default="#4fd1c5")
    border = db.Column(db.String(64), default="rgba(255,255,255,.08)")

    brand_font = db.Column(
        db.String(255),
        default="system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell",
    )


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def save_image(file_storage):
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        return None

    filename = secure_filename(file_storage.filename)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    base, ext = os.path.splitext(filename)
    c = 1
    while os.path.exists(save_path):
        filename = f"{base}_{c}{ext}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        c += 1

    file_storage.save(save_path)
    return "/static/uploads/" + filename


def get_settings() -> Settings:
    settings = Settings.query.first()
    if not settings:
        settings = Settings(
            phone="+7 (777) 123-45-67",
            bg="#121015",
            card="#181820",
            muted="#9aa3b2",
            text="#f5f7fb",
            brand="#ffbd2f",
            accent="#4fd1c5",
            border="rgba(255,255,255,.08)",
            brand_font="system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell",
        )
        db.session.add(settings)
        db.session.commit()
        return settings

    changed = False
    if not getattr(settings, "bg", None):
        settings.bg = "#121015"; changed = True
    if not getattr(settings, "card", None):
        settings.card = "#181820"; changed = True
    if not getattr(settings, "muted", None):
        settings.muted = "#9aa3b2"; changed = True
    if not getattr(settings, "text", None):
        settings.text = "#f5f7fb"; changed = True
    if not getattr(settings, "brand", None):
        settings.brand = "#ffbd2f"; changed = True
    if not getattr(settings, "accent", None):
        settings.accent = "#4fd1c5"; changed = True
    if not getattr(settings, "border", None):
        settings.border = "rgba(255,255,255,.08)"; changed = True
    if not getattr(settings, "brand_font", None):
        settings.brand_font = "system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell"
        changed = True

    if changed:
        db.session.commit()

    return settings


@app.route("/")
def index():
    menus = Menu.query.order_by(Menu.id.asc()).all()
    categories = Category.query.order_by(Category.id.asc()).all()
    dishes = Dish.query.order_by(Dish.id.asc()).all()
    settings = get_settings()

    menus_out = [
        dict(
            id=m.id,
            slug=m.slug,
            title_ru=m.title_ru,
            title_kz=m.title_kz,
            title_en=m.title_en,
            image=m.image or "",
        )
        for m in menus
    ]

    cats_out = [
        dict(
            id=c.id,
            menu_id=c.menu_id,
            slug=c.slug,
            name_ru=c.name_ru,
            name_kz=c.name_kz,
            name_en=c.name_en,
        )
        for c in categories
    ]

    dishes_out = [
        dict(
            id=d.id,
            category_id=d.category_id,
            slug=d.slug,
            title_ru=d.title_ru,
            title_kz=d.title_kz,
            title_en=d.title_en,
            price=d.price,
            ing_ru=d.ing_ru or "",
            ing_kz=d.ing_kz or "",
            ing_en=d.ing_en or "",
            image=d.image or "",
        )
        for d in dishes
    ]

    return render_template(
        "menu.html",
        menus=menus_out,
        categories=cats_out,
        items=dishes_out,
        phone=settings.phone or "",
        theme=settings,
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        expected = os.environ.get("ADMIN_PASSWORD", "admin123")
        if password == expected:
            session["is_admin"] = True
            session.permanent = True
            flash("Вы вошли как админ.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Неверный пароль", "danger")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Вы вышли.", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    settings = get_settings()

    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        if phone != "":
            settings.phone = phone

        for field in ("bg", "card", "muted", "text", "brand", "accent", "border", "brand_font"):
            val = request.form.get(field)
            if val is not None and val.strip() != "":
                setattr(settings, field, val.strip())

        db.session.commit()
        flash("Настройки обновлены", "success")
        return redirect(url_for("admin_dashboard"))

    stats = {
        "menus": Menu.query.count(),
        "categories": Menu.query.count() if False else Category.query.count(),
        "dishes": Dish.query.count(),
    }
    return render_template("admin_dashboard.html", stats=stats, settings=settings)


@app.route("/admin/menus", methods=["GET", "POST"])
def admin_menus():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            slug = request.form.get("slug", "").strip()
            ru = request.form.get("title_ru", "").strip()
            kz = request.form.get("title_kz", "").strip()
            en = request.form.get("title_en", "").strip()
            img = request.files.get("image")

            if not slug or not ru or not kz or not en:
                flash("Заполните все поля", "danger")
            else:
                if Menu.query.filter_by(slug=slug).first():
                    flash("Меню с таким slug уже существует", "danger")
                else:
                    image_path = save_image(img) if img and img.filename else ""
                    m = Menu(
                        slug=slug,
                        title_ru=ru,
                        title_kz=kz,
                        title_en=en,
                        image=image_path,
                    )
                    db.session.add(m)
                    db.session.commit()
                    flash("Меню добавлено", "success")

        elif action == "delete":
            mid = request.form.get("id")
            obj = Menu.query.get(int(mid)) if mid and mid.isdigit() else None
            if obj:
                db.session.delete(obj)
                db.session.commit()
                flash("Меню удалено", "success")

    menus = Menu.query.order_by(Menu.id.asc()).all()
    return render_template("admin_menus.html", menus=menus)


@app.route("/admin/menus/<int:menu_id>/edit", methods=["GET", "POST"])
def admin_menu_edit(menu_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    menu = Menu.query.get_or_404(menu_id)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "update":
            slug = request.form.get("slug", "").strip()
            ru = request.form.get("title_ru", "").strip()
            kz = request.form.get("title_kz", "").strip()
            en = request.form.get("title_en", "").strip()
            img = request.files.get("image")

            if not slug or not ru or not kz or not en:
                flash("Заполните все поля", "danger")
            else:
                exists = Menu.query.filter(
                    Menu.slug == slug,
                    Menu.id != menu.id
                ).first()
                if exists:
                    flash("Другое меню с таким slug уже существует", "danger")
                else:
                    menu.slug = slug
                    menu.title_ru = ru
                    menu.title_kz = kz
                    menu.title_en = en

                    if img and img.filename:
                        new_path = save_image(img)
                        if new_path:
                            menu.image = new_path

                    db.session.commit()
                    flash("Меню обновлено", "success")
                    return redirect(url_for("admin_menus"))

    return render_template("admin_menu_edit.html", menu=menu)


@app.route("/admin/categories", methods=["GET", "POST"])
def admin_categories():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    menus = Menu.query.order_by(Menu.id.asc()).all()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            menu_id = request.form.get("menu_id", "").strip()
            slug = request.form.get("slug", "").strip()
            ru = request.form.get("name_ru", "").strip()
            kz = request.form.get("name_kz", "").strip()
            en = request.form.get("name_en", "").strip()

            if not menu_id or not slug or not ru or not kz or not en:
                flash("Заполните все поля", "danger")
            else:
                if Category.query.filter_by(slug=slug).first():
                    flash("Категория с таким slug уже существует", "danger")
                else:
                    c = Category(
                        menu_id=int(menu_id),
                        slug=slug,
                        name_ru=ru,
                        name_kz=kz,
                        name_en=en,
                    )
                    db.session.add(c)
                    db.session.commit()
                    flash("Категория создана", "success")

        elif action == "delete":
            cid = request.form.get("id")
            obj = Category.query.get(int(cid)) if cid and cid.isdigit() else None
            if obj:
                db.session.delete(obj)
                db.session.commit()
                flash("Категория удалена", "success")

    cats = Category.query.order_by(Category.id.asc()).all()
    return render_template("admin_categories.html", cats=cats, menus=menus)


@app.route("/admin/categories/<int:cat_id>/edit", methods=["GET", "POST"])
def admin_category_edit(cat_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    cat = Category.query.get_or_404(cat_id)
    menus = Menu.query.order_by(Menu.id.asc()).all()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "update":
            menu_id = request.form.get("menu_id", "").strip()
            slug = request.form.get("slug", "").strip()
            ru = request.form.get("name_ru", "").strip()
            kz = request.form.get("name_kz", "").strip()
            en = request.form.get("name_en", "").strip()

            if not menu_id or not slug or not ru or not kz or not en:
                flash("Заполните все поля", "danger")
            else:
                exists = Category.query.filter(
                    Category.slug == slug,
                    Category.id != cat.id
                ).first()
                if exists:
                    flash("Другая категория с таким slug уже существует", "danger")
                else:
                    cat.menu_id = int(menu_id)
                    cat.slug = slug
                    cat.name_ru = ru
                    cat.name_kz = kz
                    cat.name_en = en
                    db.session.commit()
                    flash("Категория обновлена", "success")
                    return redirect(url_for("admin_categories"))

    return render_template("admin_category_edit.html", cat=cat, menus=menus)


@app.route("/admin/dishes", methods=["GET", "POST"])
def admin_dishes():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    cats = Category.query.order_by(Category.id.asc()).all()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            category_id = request.form.get("category_id", "").strip()
            slug = request.form.get("slug", "").strip()

            title_ru = request.form.get("title_ru", "").strip()
            title_kz = request.form.get("title_kz", "").strip()
            title_en = request.form.get("title_en", "").strip()

            price_raw = request.form.get("price", "0").strip()

            ing_ru = request.form.get("ing_ru", "").strip()
            ing_kz = request.form.get("ing_kz", "").strip()
            ing_en = request.form.get("ing_en", "").strip()

            img = request.files.get("image")

            if not category_id or not slug or not title_ru or not title_kz or not title_en:
                flash("Заполните обязательные поля", "danger")
            else:
                if Dish.query.filter_by(slug=slug).first():
                    flash("Блюдо с таким slug уже существует", "danger")
                else:
                    try:
                        price_val = int(price_raw)
                    except Exception:
                        price_val = 0

                    image_path = save_image(img) if img and img.filename else ""

                    d = Dish(
                        category_id=int(category_id),
                        slug=slug,
                        title_ru=title_ru,
                        title_kz=title_kz,
                        title_en=title_en,
                        price=price_val,
                        ing_ru=ing_ru,
                        ing_kz=ing_kz,
                        ing_en=ing_en,
                        image=image_path,
                    )
                    db.session.add(d)
                    db.session.commit()
                    flash("Блюдо добавлено", "success")

        elif action == "delete":
            did = request.form.get("id")
            obj = Dish.query.get(int(did)) if did and did.isdigit() else None
            if obj:
                db.session.delete(obj)
                db.session.commit()
                flash("Блюдо удалено", "success")

    dishes = Dish.query.order_by(Dish.id.desc()).all()
    return render_template("admin_dishes.html", dishes=dishes, cats=cats)


@app.route("/admin/dishes/<int:dish_id>/edit", methods=["GET", "POST"])
def admin_dish_edit(dish_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    dish = Dish.query.get_or_404(dish_id)
    cats = Category.query.order_by(Category.id.asc()).all()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "update":
            category_id = request.form.get("category_id", "").strip()
            slug = request.form.get("slug", "").strip()

            title_ru = request.form.get("title_ru", "").strip()
            title_kz = request.form.get("title_kz", "").strip()
            title_en = request.form.get("title_en", "").strip()

            price_raw = request.form.get("price", "0").strip()

            ing_ru = request.form.get("ing_ru", "").strip()
            ing_kz = request.form.get("ing_kz", "").strip()
            ing_en = request.form.get("ing_en", "").strip()

            img = request.files.get("image")

            if not category_id or not slug or not title_ru or not title_kz or not title_en:
                flash("Заполните обязательные поля", "danger")
            else:
                exists = Dish.query.filter(
                    Dish.slug == slug,
                    Dish.id != dish.id
                ).first()
                if exists:
                    flash("Другое блюдо с таким slug уже существует", "danger")
                else:
                    dish.category_id = int(category_id)
                    dish.slug = slug
                    dish.title_ru = title_ru
                    dish.title_kz = title_kz
                    dish.title_en = title_en

                    try:
                        dish.price = int(price_raw)
                    except Exception:
                        dish.price = 0

                    dish.ing_ru = ing_ru
                    dish.ing_kz = ing_kz
                    dish.ing_en = ing_en

                    if img and img.filename:
                        new_path = save_image(img)
                        if new_path:
                            dish.image = new_path

                    db.session.commit()
                    flash("Блюдо обновлено", "success")
                    return redirect(url_for("admin_dishes"))

    return render_template("admin_dish_edit.html", dish=dish, cats=cats)


@app.route("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.cli.command("init-db")
def init_db_cmd():
    db.create_all()

    if not Settings.query.first():
        db.session.add(Settings(phone="+7 (777) 123-45-67"))
        db.session.commit()

    if not Menu.query.first():
        main = Menu(
            slug="main",
            title_ru="Основное меню",
            title_kz="Негізгі мәзір",
            title_en="Main menu",
            image="https://images.unsplash.com/photo-1604908176997-1251884b08a3?q=80&w=800",
        )
        bar = Menu(
            slug="bar",
            title_ru="Барное меню",
            title_kz="Бар мәзірі",
            title_en="Bar menu",
            image="https://images.unsplash.com/photo-1514933651103-005eec06c04b?q=80&w=800",
        )
        wine = Menu(
            slug="wine",
            title_ru="Винная карта",
            title_kz="Шарап картасы",
            title_en="Wine list",
            image="https://images.unsplash.com/photo-1510626176961-4b57d4fbad03?q=80&w=800",
        )
        db.session.add_all([main, bar, wine])
        db.session.commit()

        cat_breakfast = Category(
            menu_id=main.id,
            slug="breakfast",
            name_ru="Завтраки",
            name_kz="Таңғы ас",
            name_en="Breakfasts",
        )
        cat_salad = Category(
            menu_id=main.id,
            slug="salads",
            name_ru="Салаты",
            name_kz="Салаттар",
            name_en="Salads",
        )
        db.session.add_all([cat_breakfast, cat_salad])
        db.session.commit()

        d1 = Dish(
            category_id=cat_breakfast.id,
            slug="turkish-breakfast",
            title_ru="Турецкий завтрак на одного",
            title_kz="Бір адамға түрік таңғы асы",
            title_en="Turkish breakfast for one",
            price=7990,
            ing_ru="сыр, оливки, овощи, яйца, лепёшка",
            ing_kz="ірімшік, зәйтүн, көкөністер, жұмыртқа, нан",
            ing_en="cheese, olives, veggies, eggs, flatbread",
            image="https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?q=80&w=800",
        )
        d2 = Dish(
            category_id=cat_salad.id,
            slug="greek-salad",
            title_ru="Греческий салат",
            title_kz="Грек салаты",
            title_en="Greek salad",
            price=4590,
            ing_ru="помидоры, огурцы, фета, оливки",
            ing_kz="қызанақ, қияр, фета, зәйтүн",
            ing_en="tomatoes, cucumbers, feta, olives",
            image="https://images.unsplash.com/photo-1569058242253-92a9c755a0f4?q=80&w=800",
        )
        db.session.add_all([d1, d2])
        db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)