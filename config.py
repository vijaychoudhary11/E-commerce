import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "fashion-store-secret-key"

    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{os.path.join(BASE_DIR, 'database', 'store.db')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        "static",
        "uploads",
        "products"
    )

    # Razorpay
    RAZORPAY_KEY_ID = "rzp_test_TIusKMufjjLQf0"
    RAZORPAY_KEY_SECRET = "hG50JJkG7xamxpoN4UapaISc"