from datetime import datetime
from extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    slug = db.Column(
        db.String(200),
        nullable=False,
        unique=True,
        index=True
    )

    description = db.Column(db.Text)

    image = db.Column(db.String(255))

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    products = db.relationship(
        "Product",
        back_populates="category",
        lazy=True,
        cascade="all, delete"
    )

    def __repr__(self):
        return f"<Category {self.name}>"