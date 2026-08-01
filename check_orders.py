from app import app
from models.product import Product

with app.app_context():
    products = Product.query.all()

    for p in products:
        print(p.name)
        print("IMAGE:", p.image_1)