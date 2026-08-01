import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "fashion-store-secret-key"
    )

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'database', 'store.db')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        "static",
        "uploads",
        "products"
    )

    RAZORPAY_KEY_ID = os.environ.get(
        "RAZORPAY_KEY_ID"
    )

    RAZORPAY_KEY_SECRET = os.environ.get(
        "RAZORPAY_KEY_SECRET"
    )