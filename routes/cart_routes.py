from flask import Blueprint, render_template, redirect, url_for, session
from models.product import Product

from flask import Blueprint, render_template, redirect, url_for, session, request , flash
from flask import request
from models.order import Order
from models.order_item import OrderItem
from extensions import db
import uuid

import razorpay
from flask import current_app

cart_bp = Blueprint("cart", __name__)

@cart_bp.route("/cart")
def cart():

    cart = session.get("cart", {})

    cart_products = []

    total = 0

    for product_id, quantity in cart.items():

        product = Product.query.get(int(product_id))

        if product:

            subtotal = product.price * quantity

            total += subtotal

            cart_products.append({
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal
            })

    return render_template(
        "cart.html",
        cart_products=cart_products,
        total=total
    )

@cart_bp.route("/cart/add/<int:product_id>")
def add_to_cart(product_id):

    product = Product.query.get_or_404(product_id)

    if product.stock <= 0:
        flash("This product is out of stock.", "danger")
        return redirect(url_for("home"))

    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]

    product_id = str(product_id)

    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1

    session["cart"] = cart

    return redirect(url_for("cart.cart"))

@cart_bp.route("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):

    if "cart" not in session:
        return redirect(url_for("cart.cart"))

    cart = session["cart"]

    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]

    session["cart"] = cart

    return redirect(url_for("cart.cart"))

@cart_bp.route("/checkout", methods=["GET", "POST"])
def checkout():

    print("Checkout Session:", dict(session))

    # Customer must be logged in
    if "customer_id" not in session:
        flash("Please login to place your order.", "warning")
        return redirect(
            url_for(
                "customer.login",
                next=url_for("cart.checkout")
            )
        )

    # Cart empty check
    if "cart" not in session or len(session["cart"]) == 0:
        return redirect(url_for("cart.cart"))

    if request.method == "POST":

        session["checkout_data"] = {
            "customer_name": request.form.get("customer_name"),
            "customer_phone": request.form.get("customer_phone"),
            "address": request.form.get("address")
        }

        return redirect(url_for("cart.payment"))

    return render_template("checkout.html")


@cart_bp.route("/payment")
def payment():

    if "checkout_data" not in session:
        return redirect(url_for("cart.checkout"))

    checkout_data = session["checkout_data"]
    cart = session.get("cart", {})

    cart_products = []

    subtotal = 0
    total_quantity = 0

    for product_id, quantity in cart.items():

        product = Product.query.get(int(product_id))

        if product:

            subtotal += product.price * quantity
            total_quantity += quantity

            cart_products.append({
                "product": product,
                "quantity": quantity
            })

    delivery_charge = 49
    grand_total = subtotal + delivery_charge

    return render_template(
        "payment.html",
        checkout_data=checkout_data,
        cart_products=cart_products,
        subtotal=subtotal,
        delivery_charge=delivery_charge,
        grand_total=grand_total,
        total_products=len(cart_products),
        total_quantity=total_quantity
    )

@cart_bp.route("/process-payment", methods=["POST"])
def process_payment():

    if "checkout_data" not in session:
        return redirect(url_for("cart.checkout"))

    checkout_data = session["checkout_data"]
    cart = session.get("cart", {})

    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart.cart"))

    payment_method = request.form.get("payment_method")

    subtotal = 0

    for product_id, quantity in cart.items():

        product = Product.query.get(int(product_id))

        if product:
            subtotal += product.price * quantity

    delivery_charge = 49
    grand_total = subtotal + delivery_charge

    # =======================
    # CASH ON DELIVERY
    # =======================

    if payment_method == "COD":

        try:

            create_order(
                customer_id=session["customer_id"],
                checkout_data=checkout_data,
                cart=cart,
                payment_method="COD",
                payment_status="Pending",
                subtotal=subtotal,
                grand_total=grand_total
            )

        except ValueError as e:

            flash(str(e), "danger")
            return redirect(url_for("cart.cart"))

        session.pop("cart", None)
        session.pop("checkout_data", None)

        return redirect(url_for("cart.order_success"))

    # =======================
    # RAZORPAY
    # =======================

    client = razorpay.Client(
        auth=(
            current_app.config["RAZORPAY_KEY_ID"],
            current_app.config["RAZORPAY_KEY_SECRET"]
        )
    )

    payment = client.order.create({
        "amount": int(grand_total * 100),
        "currency": "INR",
        "payment_capture": 1
    })

    return render_template(
        "payment_gateway.html",
        razorpay_order_id=payment["id"],
        razorpay_key=current_app.config["RAZORPAY_KEY_ID"],
        amount=int(grand_total * 100)
    )

@cart_bp.route("/payment-success", methods=["POST"])
def payment_success():

    if "checkout_data" not in session:
        return redirect(url_for("cart.checkout"))

    checkout_data = session["checkout_data"]
    cart = session.get("cart", {})

    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart.cart"))

    razorpay_payment_id = request.form.get("razorpay_payment_id")
    razorpay_order_id = request.form.get("razorpay_order_id")
    razorpay_signature = request.form.get("razorpay_signature")

    client = razorpay.Client(
        auth=(
            current_app.config["RAZORPAY_KEY_ID"],
            current_app.config["RAZORPAY_KEY_SECRET"]
        )
    )

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })

    except Exception:
        flash("Payment verification failed.", "danger")
        return redirect(url_for("cart.payment"))

    subtotal = 0

    for product_id, quantity in cart.items():

        product = Product.query.get(int(product_id))

        if not product:
            continue

        subtotal += product.price * quantity

    delivery_charge = 49
    grand_total = subtotal + delivery_charge

    try:

        create_order(
            customer_id=session["customer_id"],
            checkout_data=checkout_data,
            cart=cart,
            payment_method="Razorpay",
            payment_status="Paid",
            subtotal=subtotal,
            grand_total=grand_total,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_order_id=razorpay_order_id
        )

    except ValueError as e:

        flash(str(e), "danger")
        return redirect(url_for("cart.cart"))

        session.pop("cart", None)
        session.pop("checkout_data", None)

        return redirect(url_for("cart.order_success"))

@cart_bp.route("/order-success")
def order_success():

    return render_template("order_success.html")

@cart_bp.route("/cart/update/<int:product_id>", methods=["POST"])
def update_cart(product_id):

    if "cart" not in session:
        return redirect(url_for("cart.cart"))

    cart = session["cart"]

    quantity = int(request.form.get("quantity"))

    product_id = str(product_id)

    if product_id in cart:

        if quantity <= 0:
            del cart[product_id]
        else:
            cart[product_id] = quantity

    session["cart"] = cart

    return redirect(url_for("cart.cart"))

@cart_bp.route("/track-order", methods=["GET", "POST"])
def track_order():

    order = None

    if request.method == "POST":
        order_number = request.form.get("order_number")

        order = Order.query.filter_by(
            order_number=order_number
        ).first()

    return render_template(
        "track_order.html",
        order=order
    )


def create_order(
    customer_id,
    checkout_data,
    cart,
    payment_method,
    payment_status,
    subtotal,
    grand_total,
    razorpay_payment_id=None,
    razorpay_order_id=None
):

    order = Order(
        customer_id=customer_id,
        order_number=str(uuid.uuid4())[:8],
        customer_name=checkout_data["customer_name"],
        customer_phone=checkout_data["customer_phone"],
        address=checkout_data["address"],
        subtotal=subtotal,
        grand_total=grand_total,
        payment_method=payment_method,
        payment_status=payment_status,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_order_id=razorpay_order_id
    )

    db.session.add(order)
    db.session.commit()

    for product_id, quantity in cart.items():

        product = Product.query.get(int(product_id))

        if product:

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price,
                total_price=product.price * quantity
            )

            db.session.add(order_item)

            if product.stock < quantity:

              raise ValueError(
        f"{product.name} has only {product.stock} items left in stock."
    )

    product.stock -= quantity

    db.session.commit()

    return order