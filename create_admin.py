from app import app
from extensions import db
from models.admin import Admin

with app.app_context():

    admin = Admin(
        username="admin",
        email="admin@example.com"
    )

    admin.set_password("admin123")

    db.session.add(admin)
    db.session.commit()

    print("Admin Created Successfully")