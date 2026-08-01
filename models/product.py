from datetime import datetime
from extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=False
    )

    name = db.Column(
        db.String(255),
        nullable=False
    )

    slug = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
        index=True
    )

    description = db.Column(
        db.Text
    )

    sku = db.Column(
        db.String(100),
        unique=True
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    stock = db.Column(
    db.Integer,
    default=0,
    nullable=False
)

    sale_price = db.Column(
        db.Float
    )

    stock = db.Column(
        db.Integer,
        default=0
    )

    featured = db.Column(
        db.Boolean,
        default=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    reviews = db.relationship(
    "Review",
    backref="product",
    lazy=True,
    cascade="all, delete-orphan"
)


    @property
    def average_rating(self):
        if not self.reviews:
            return 0

        total = sum(review.rating for review in self.reviews)
        return round(total / len(self.reviews), 1)
    
 # Product Images
    image_1 = db.Column(db.String(255))
    image_2 = db.Column(db.String(255))
    image_3 = db.Column(db.String(255))
    image_4 = db.Column(db.String(255))

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    category = db.relationship(
        "Category",
        back_populates="products"
    )

    order_items = db.relationship(
        "OrderItem",
        back_populates="product",
        lazy=True
    )

    @property
    def current_price(self):
        return self.sale_price if self.sale_price else self.price

    def __repr__(self):
        return f"<Product {self.name}>"