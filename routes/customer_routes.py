from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models.customer import Customer
from models.order import Order
from models.review import Review

customer_bp = Blueprint("customer", __name__)


# ---------------- REGISTER ----------------

@customer_bp.route("/customer/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        password = request.form["password"]

        if Customer.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return redirect(url_for("customer.register"))

        customer = Customer(
            full_name=full_name,
            email=email,
            mobile=mobile,
            password=generate_password_hash(password)
        )

        db.session.add(customer)
        db.session.commit()

        flash("Registration Successful! Please Login.", "success")
        return redirect(url_for("customer.login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------

@customer_bp.route("/customer/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        customer = Customer.query.filter_by(email=email).first()

        if customer and check_password_hash(customer.password, password):

            session["customer_id"] = customer.id
            session["customer_name"] = customer.full_name

            flash("Login Successful!", "success")

            next_page = request.args.get("next")

            if next_page:
                return redirect(next_page)

            return redirect(url_for("home"))

        flash("Invalid Email or Password", "danger")

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@customer_bp.route("/customer/logout")
def logout():

    session.pop("customer_id", None)
    session.pop("customer_name", None)

    flash("Logged Out Successfully", "success")

    return redirect(url_for("customer.login"))


# ---------------- PROFILE ----------------

@customer_bp.route("/customer/profile")
def profile():

    if "customer_id" not in session:
        return redirect(url_for("customer.login"))

    customer = Customer.query.get(session["customer_id"])

    return render_template(
        "profile.html",
        customer=customer
    )


# ---------------- EDIT PROFILE ----------------

@customer_bp.route("/customer/profile/edit", methods=["GET", "POST"])
def edit_profile():

    if "customer_id" not in session:
        return redirect(url_for("customer.login"))

    customer = Customer.query.get(session["customer_id"])

    if request.method == "POST":

        customer.full_name = request.form.get("full_name")
        customer.email = request.form.get("email")
        customer.mobile = request.form.get("mobile")

        db.session.commit()

        flash("Profile Updated Successfully", "success")

        return redirect(url_for("customer.profile"))

    return render_template(
        "edit_profile.html",
        customer=customer
    )


# ---------------- ORDER HISTORY ----------------

@customer_bp.route("/customer/orders")
def order_history():

    if "customer_id" not in session:
        return redirect(url_for("customer.login"))

    orders = Order.query.filter_by(
        customer_id=session["customer_id"]
    ).order_by(
        Order.id.desc()
    ).all()

    return render_template(
        "order_history.html",
        orders=orders
    )


# ---------------- ADD REVIEW ----------------

@customer_bp.route("/customer/review/<int:product_id>", methods=["POST"])
def add_review(product_id):

    if "customer_id" not in session:
        return redirect(url_for("customer.login"))

    review = Review(
        product_id=product_id,
        customer_id=session["customer_id"],
        rating=int(request.form.get("rating")),
        comment=request.form.get("comment")
    )

    db.session.add(review)
    db.session.commit()

    return redirect(url_for("product_detail", id=product_id))