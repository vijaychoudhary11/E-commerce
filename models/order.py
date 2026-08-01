from datetime import datetime
from extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(
    db.Integer,
    db.ForeignKey("customers.id"),
    nullable=False
)
 
    order_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    customer_name = db.Column(
        db.String(200),
        nullable=False
    )

    customer_email = db.Column(
        db.String(150)
    )

    customer_phone = db.Column(
        db.String(20),
        nullable=False
    )

    address = db.Column(
        db.Text,
        nullable=False
    )

    city = db.Column(
        db.String(100)
    )

    state = db.Column(
        db.String(100)
    )

    pincode = db.Column(
        db.String(20)
    )

    subtotal = db.Column(
        db.Float,
        nullable=False
    )

    shipping_charge = db.Column(
        db.Float,
        default=0
    )

    grand_total = db.Column(
        db.Float,
        nullable=False
    )

    status = db.Column(db.String(50), default="Pending")

    payment_method = db.Column(
        db.String(50),
        default="COD"
    )

    razorpay_payment_id = db.Column(
    db.String(100)
    )

    razorpay_order_id = db.Column(
    db.String(100)
    )

    payment_status = db.Column(
        db.String(50),
        default="Pending"
    )

    order_status = db.Column(
        db.String(50),
        default="Pending"
    )

    notes = db.Column(
        db.Text
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

    items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<Order {self.order_number}>"