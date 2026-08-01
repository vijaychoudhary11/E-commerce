import os
from datetime import datetime
from werkzeug.utils import secure_filename

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from extensions import db

from models.admin import Admin
from models.category import Category
from models.product import Product
from models.order import Order
from models.order_item import OrderItem
from models.review import Review

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        admin = Admin.query.filter_by(
            email=email
        ).first()

        print("EMAIL:", email)
        print("ADMIN:", admin)

        if admin:
            print(
                "PASSWORD CHECK:",
                admin.check_password(password)
            )

        if admin and admin.check_password(password):

            session["admin_id"] = admin.id

            return redirect(
                url_for("admin.dashboard")
            )

        flash("Invalid Email or Password")

    return render_template(
        "admin/login.html"
    )


@admin_bp.route("/dashboard")
def dashboard():

    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

    total_products = Product.query.count()

    total_orders = Order.query.count()

    total_revenue = db.session.query(
        db.func.sum(Order.grand_total)
    ).scalar() or 0

    from sqlalchemy import func
    from models.order_item import OrderItem

    top_selling_products = (
    db.session.query(
        Product,
        func.sum(OrderItem.quantity).label("total_sold")
    )
    .join(OrderItem, Product.id == OrderItem.product_id)
    .group_by(Product.id)
    .order_by(func.sum(OrderItem.quantity).desc())
    .limit(8)
    .all()
)

    pending_orders = Order.query.filter_by(
        order_status="Pending"
    ).count()

    delivered_orders = Order.query.filter_by(
        order_status="Delivered"
    ).count()

    confirmed_orders = Order.query.filter_by(
        order_status="Confirmed"
    ).count()

    shipped_orders = Order.query.filter_by(
        order_status="Shipped"
    ).count()

    recent_orders = Order.query.order_by(
        Order.id.desc()
    ).limit(5).all()

    low_stock_products = Product.query.filter(
        Product.stock <= 5
    ).count()

    months = [
        "Jan", "Feb", "Mar",
        "Apr", "May", "Jun",
        "Jul", "Aug", "Sep",
        "Oct", "Nov", "Dec"
    ]

    sales = []

    all_orders = Order.query.all()

    for month in range(1, 13):

        revenue = 0

        for order in all_orders:

            if order.created_at and order.created_at.month == month:
                revenue += order.grand_total

        sales.append(revenue)

    return render_template(
        "admin/dashboard.html",
        total_products=total_products,
        total_orders=total_orders,
        total_revenue=total_revenue,
        pending_orders=pending_orders,
        delivered_orders=delivered_orders,
        recent_orders=recent_orders,
        months=months,
        sales=sales,
        low_stock_products=low_stock_products,
        confirmed_orders=confirmed_orders,
        shipped_orders=shipped_orders,
        top_selling_products=top_selling_products
    )


  
@admin_bp.route("/admin/logout")
def logout():

    session.clear()

    return redirect(url_for("admin.admin_login"))

@admin_bp.route("/admin/categories")
def categories():

    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

    all_categories = Category.query.all()

    return render_template(
        "admin/categories.html",
        categories=all_categories
    )


@admin_bp.route("/admin/category/add", methods=["GET", "POST"])
def add_category():

    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

    if request.method == "POST":

        name = request.form.get("name")
        slug = request.form.get("slug")
        description = request.form.get("description")

        category = Category(
            name=name,
            slug=slug,
            description=description
        )

        db.session.add(category)
        db.session.commit()

        return redirect(url_for("admin.categories"))

    return render_template("admin/add_category.html")

@admin_bp.route("/category/edit/<int:id>", methods=["GET", "POST"])
def edit_category(id):

    category = Category.query.get_or_404(id)

    if request.method == "POST":
        category.name = request.form["name"]
        category.slug = request.form["slug"]

        db.session.commit()

        flash("Category Updated Successfully", "success")
        return redirect(url_for("admin.categories"))

    return render_template(
        "admin/edit_category.html",
        category=category
    )

@admin_bp.route("/category/delete/<int:id>")
def delete_category(id):

    category = Category.query.get_or_404(id)

    db.session.delete(category)
    db.session.commit()

    flash("Category Deleted Successfully", "success")

    return redirect(url_for("admin.categories"))

@admin_bp.route("/admin/products")
def products():

    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

    all_products = Product.query.all()

    return render_template(
        "admin/products.html",
        products=all_products
    )

@admin_bp.route("/admin/reviews")
def reviews():

    reviews = Review.query.order_by(
        Review.id.desc()
    ).all()

    return render_template(
        "admin/reviews.html",
        reviews=reviews
    )

@admin_bp.route("/admin/product/delete/<int:id>")
def delete_product(id):

    Review.query.filter_by(product_id=id).delete()

    OrderItem.query.filter_by(product_id=id).delete()

    product = Product.query.get_or_404(id)

    db.session.delete(product)
    db.session.commit()

    return redirect(url_for("admin.products"))


@admin_bp.route("/admin/product/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

    product = Product.query.get_or_404(id)

    if request.method == "POST":

        product.name = request.form.get("name")
        product.slug = request.form.get("slug")
        product.description = request.form.get("description")
        product.price = request.form.get("price")
        product.stock = request.form.get("stock")

        db.session.commit()

        return redirect(url_for("admin.products"))

    return render_template(
        "admin/edit_product.html",
        product=product
    )

@admin_bp.route("/admin/product/add", methods=["GET", "POST"])
def add_product():

    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

    categories = Category.query.all()

    if request.method == "POST":

        image = request.files.get("image")

        filename = None

        if image and image.filename:
            filename= secure_filename(image.filename)

            image.save(
                os.path.join(
                    "static/uploads/products",
                    filename
                )
            )

        product = Product(
            name=request.form.get("name"),
            slug=request.form.get("slug"),
            description=request.form.get("description"),
            price=request.form.get("price"),
            stock = int(request.form.get("stock", 0)),
            category_id=request.form.get("category_id"),
            image_1=filename
        )

    

        db.session.add(product)
        db.session.commit()

        return redirect(url_for("admin.products"))

    return render_template(
        "admin/add_product.html",
        categories=categories
    )

@admin_bp.route("/admin/orders")
def orders():

    orders = Order.query.order_by(Order.id.desc()).all()

    return render_template(
        "admin/orders.html",
        orders=orders
    )

@admin_bp.route("/admin/customers")
def customers():

    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

    search = request.args.get("search", "")

    customers = Order.query

    if search:
        customers = customers.filter(
            Order.customer_name.contains(search)
        )

    customers = customers.order_by(
        Order.id.desc()
    ).all()

    return render_template(
        "admin/customers.html",
        customers=customers,
        search=search
    )

@admin_bp.route("/admin/reports")
def reports():

    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

    orders = Order.query.order_by(
        Order.id.desc()
    ).all()

    total_sales = sum(
        order.grand_total
        for order in orders
    )

    total_orders = len(orders)

    return render_template(
        "admin/reports.html",
        orders=orders,
        total_sales=total_sales,
        total_orders=total_orders
    )

@admin_bp.route("/admin/profile")
def admin_profile():

    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

    admin = Admin.query.get(session["admin_id"])

    return render_template(
        "admin/profile.html",
        admin=admin
    )

@admin_bp.route("/admin/change-password", methods=["GET", "POST"])
def change_password():

    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

    admin = Admin.query.get(session["admin_id"])

    if request.method == "POST":

        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not admin.check_password(old_password):
            flash("Old password is incorrect")
            return redirect(url_for("admin.change_password"))

        if new_password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("admin.change_password"))

        admin.set_password(new_password)

        db.session.commit()

        flash("Password changed successfully")

        return redirect(url_for("admin.admin_profile"))

    return render_template(
        "admin/change_password.html"
    )

@admin_bp.route("/admin/edit-profile", methods=["GET", "POST"])
def edit_profile():

    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

    admin = Admin.query.get(session["admin_id"])

    if request.method == "POST":

        admin.username = request.form.get("username")
        admin.email = request.form.get("email")

        db.session.commit()

        flash("Profile updated successfully")

        return redirect(url_for("admin.admin_profile"))

    return render_template(
        "admin/edit_profile.html",
        admin=admin
    )

@admin_bp.route("/admin/customer/<int:order_id>")
def customer_details(order_id):

    if "admin_id" not in session:
        return redirect(url_for("admin.admin_login"))

    customer = Order.query.get_or_404(order_id)

    return render_template(
        "admin/customer_details.html",
        customer=customer
    )

@admin_bp.route("/admin/orders/<int:order_id>")
def order_details(order_id):

    order = Order.query.get_or_404(order_id)

    return render_template(
        "admin/order_details.html",
        order=order
    )


@admin_bp.route("/admin/orders/update-status/<int:order_id>", methods=["POST"])
def update_order_status(order_id):

    order = Order.query.get_or_404(order_id)

    new_status = request.form.get("order_status")

    order.order_status = new_status

    db.session.commit()

    return redirect(
        url_for(
            "admin.order_details",
            order_id=order.id
        )
    )


