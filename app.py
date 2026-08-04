from flask import Flask, render_template, request, session
from config import Config
from extensions import db

from models.cart_item import CartItem
from models.admin import Admin
from models.category import Category
from models.product import Product
from models.order import Order
from models.order_item import OrderItem
from models.review import Review
from models.customer import Customer

from routes.admin_routes import admin_bp
from routes.cart_routes import cart_bp
from routes.customer_routes import customer_bp

import os

import cloudinary
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

print("Cloud:", os.getenv("CLOUDINARY_CLOUD_NAME"))
print("Key:", os.getenv("CLOUDINARY_API_KEY"))
print("Secret:", os.getenv("CLOUDINARY_API_SECRET"))


app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads/products"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config.from_object(Config)

db.init_app(app)

app.secret_key = "your-secret-key"

app.register_blueprint(admin_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(customer_bp)


@app.context_processor
def cart_count():
    cart = session.get("cart", {})
    count = sum(cart.values())
    return dict(cart_count=count)


@app.route("/")
def home():

    search = request.args.get("search", "")
    category_id = request.args.get("category")

    products = Product.query

    if search:
        products = products.filter(
            Product.name.ilike(f"%{search}%")
        )

    if category_id:
        products = products.filter_by(
            category_id=category_id
        )

    products = products.all()
    categories = Category.query.all()

    return render_template(
        "products.html",
        products=products,
        categories=categories
    )


@app.route("/product/<int:id>")
def product_detail(id):

    product = Product.query.get_or_404(id)

    reviews = Review.query.filter_by(
        product_id=id
    ).all()

    return render_template(
        "product_detail.html",
        product=product,
        reviews=reviews
    )


with app.app_context():

    db.create_all()

    admin = Admin.query.filter_by(
        email="admin@gmail.com"
    ).first()

    if not admin:

        admin = Admin(
            username="admin",
            email="admin@gmail.com"
        )

        admin.set_password("admin123")

        db.session.add(admin)
        db.session.commit()

        print("Default Admin Created")

    print(Admin.query.all())


if __name__ == "__main__":

    print(app.url_map)

    app.run(debug=True)