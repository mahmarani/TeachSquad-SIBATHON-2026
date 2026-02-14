from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

# ===================== FILE PATHS =====================
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
CARTS_FILE = os.path.join(DATA_DIR, "carts.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
REVIEWS_FILE = os.path.join(DATA_DIR, "reviews.json")
WISHLIST_FILE = os.path.join(DATA_DIR, "wishlist.json")


# ===================== ENSURE FILES EXIST =====================
def ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f)

    if not os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "w") as f:
            json.dump([], f)

    if not os.path.exists(CARTS_FILE):
        with open(CARTS_FILE, "w") as f:
            json.dump({}, f)

    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "w") as f:
            json.dump([], f)

    # ✅ reviews.json
    if not os.path.exists(REVIEWS_FILE):
        with open(REVIEWS_FILE, "w") as f:
            json.dump([], f)

    # ✅ wishlist.json
    if not os.path.exists(WISHLIST_FILE):
        with open(WISHLIST_FILE, "w") as f:
            json.dump({}, f)


# ===================== JSON HELPERS =====================
def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===================== AUTH HELPERS =====================
def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    users = read_json(USERS_FILE, [])
    return next((u for u in users if u["id"] == uid), None)


def require_login():
    if not current_user():
        flash("Please login first.")
        return redirect(url_for("login"))
    return None


# ===================== PRODUCTS HELPERS =====================
def get_products():
    return read_json(PRODUCTS_FILE, [])


def get_product(pid: int):
    return next((p for p in get_products() if p["id"] == pid), None)


# ===================== CART HELPERS =====================
def get_cart_for_user(uid: int):
    carts = read_json(CARTS_FILE, {})
    return carts.get(str(uid), {})


def save_cart_for_user(uid: int, cart: dict):
    carts = read_json(CARTS_FILE, {})
    carts[str(uid)] = cart
    write_json(CARTS_FILE, carts)


def cart_count(uid: int):
    cart = get_cart_for_user(uid)
    return sum(int(q) for q in cart.values())


def cart_items_detailed(uid: int):
    cart = get_cart_for_user(uid)  # {product_id: qty}
    products = get_products()
    items = []
    total = 0

    for pid_str, qty in cart.items():
        pid = int(pid_str)
        product = next((p for p in products if p["id"] == pid), None)
        if not product:
            continue

        qty = int(qty)
        line_total = qty * int(product["price"])
        total += line_total

        items.append({
            "id": pid,
            "name": product["name"],
            "price": int(product["price"]),
            "image": product.get("image", ""),
            "qty": qty,
            "line_total": line_total
        })

    return items, total


# ===================== REVIEWS HELPERS =====================
def load_reviews():
    return read_json(REVIEWS_FILE, [])


def save_reviews(reviews):
    write_json(REVIEWS_FILE, reviews)


def get_product_reviews(product_id: int):
    reviews = load_reviews()
    return [r for r in reviews if int(r.get("product_id")) == int(product_id)]


def get_avg_rating(product_id: int):
    reviews = get_product_reviews(product_id)
    if not reviews:
        return 0
    return round(sum(int(r["rating"]) for r in reviews) / len(reviews), 1)


def user_purchased_product(user_id: int, product_id: int):
    orders = read_json(ORDERS_FILE, [])
    for o in orders:
        if int(o.get("user_id")) == int(user_id):
            for item in o.get("items", []):
                # your order items store product id in "id"
                if int(item.get("id")) == int(product_id):
                    return True
    return False


# ===================== WISHLIST HELPERS =====================
def get_wishlist(uid):
    data = read_json(WISHLIST_FILE, {})
    return data.get(str(uid), [])


def save_wishlist(uid, wishlist):
    data = read_json(WISHLIST_FILE, {})
    data[str(uid)] = wishlist
    write_json(WISHLIST_FILE, data)


def is_in_wishlist(uid, pid):
    return pid in get_wishlist(uid)


# ===================== GLOBAL NAV DATA =====================
@app.context_processor
def inject_globals():
    user = current_user()
    count = cart_count(user["id"]) if user else 0
    return {"nav_user": user, "nav_cart_count": count}


# ===================== HOME (SEARCH + FILTERS + SORT) =====================
@app.route("/")
def home():
    q = request.args.get("q", "").strip().lower()
    brand = request.args.get("brand", "")
    category = request.args.get("category", "")
    sort = request.args.get("sort", "")

    products = get_products()

    if q:
        products = [p for p in products if q in p["name"].lower() or q in p["brand"].lower()]

    if brand:
        products = [p for p in products if p.get("brand") == brand]

    if category:
        products = [p for p in products if p.get("category") == category]

    if sort == "price_asc":
        products = sorted(products, key=lambda x: int(x["price"]))
    elif sort == "price_desc":
        products = sorted(products, key=lambda x: int(x["price"]), reverse=True)

    all_products = get_products()
    brands = sorted(list(set(p.get("brand", "") for p in all_products if p.get("brand"))))
    categories = sorted(list(set(p.get("category", "") for p in all_products if p.get("category"))))

    # ⭐ ADD THIS PART
    user = current_user()
    wishlist = get_wishlist(user["id"]) if user else []

    return render_template(
        "home.html",
        products=products,
        wishlist=wishlist,
        q=q,
        brand=brand,
        category=category,
        sort=sort,
        brands=brands,
        categories=categories
    )


# ===================== PRODUCT PAGE (REVIEWS + WISHLIST) =====================
@app.route("/product/<int:pid>")
def product(pid):
    phone = get_product(pid)
    if not phone:
        return "Product not found", 404

    reviews = get_product_reviews(pid)
    avg_rating = get_avg_rating(pid)

    user = current_user()
    can_review = False
    wishlisted = False

    if user:
        can_review = user_purchased_product(user["id"], pid)
        wishlisted = is_in_wishlist(user["id"], pid)

    return render_template(
        "product.html",
        phone=phone,
        reviews=reviews,
        avg_rating=avg_rating,
        can_review=can_review,
        wishlisted=wishlisted
    )


# ===================== ADD REVIEW =====================
@app.route("/add_review/<int:product_id>", methods=["POST"])
def add_review(product_id):
    user = current_user()
    if not user:
        flash("Please login first.")
        return redirect(url_for("login"))

    if not user_purchased_product(user["id"], product_id):
        flash("You can only review products you purchased.")
        return redirect(url_for("product", pid=product_id))

    rating = request.form.get("rating", "").strip()
    comment = request.form.get("comment", "").strip()

    if not rating or not comment:
        flash("Please provide rating and comment.")
        return redirect(url_for("product", pid=product_id))

    rating_int = int(rating)
    if rating_int < 1 or rating_int > 5:
        flash("Rating must be between 1 and 5.")
        return redirect(url_for("product", pid=product_id))

    reviews = load_reviews()

    # prevent duplicate review
    for r in reviews:
        if int(r.get("user_id")) == int(user["id"]) and int(r.get("product_id")) == int(product_id):
            flash("You already reviewed this product.")
            return redirect(url_for("product", pid=product_id))

    reviews.append({
        "product_id": product_id,
        "user_id": user["id"],
        "rating": rating_int,
        "comment": comment,
        "date": datetime.now().strftime("%Y-%m-%d")
    })
    save_reviews(reviews)

    flash("Review added successfully!")
    return redirect(url_for("product", pid=product_id))


# ===================== WISHLIST API + PAGE =====================
@app.route("/toggle_wishlist/<int:pid>")
def toggle_wishlist(pid):
    user_id = session.get("user_id")
    if not user_id:
        return "login"

    with open(WISHLIST_FILE, "r") as f:
        wishlist = json.load(f)

    uid = str(user_id)
    if uid not in wishlist:
        wishlist[uid] = []

    if pid in wishlist[uid]:
        wishlist[uid].remove(pid)
        message = "removed"
    else:
        wishlist[uid].append(pid)
        message = "added"

    with open(WISHLIST_FILE, "w") as f:
        json.dump(wishlist, f, indent=2)

    return jsonify({"status": message})



@app.route("/wishlist")
def wishlist_page():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    ids = get_wishlist(user["id"])
    products = [p for p in get_products() if p["id"] in ids]
    return render_template("wishlist.html", products=products)


# ===================== LOGIN / REGISTER =====================
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    action = request.form.get("action")
    username = request.form.get("username","").strip()
    password = request.form.get("password","").strip()

    users = read_json(USERS_FILE, [])

    # -------- REGISTER --------
    if action == "register":

        if not username or not password:
            flash("Fill all fields")
            return redirect(url_for("login"))

        if any(u["username"].lower()==username.lower() for u in users):
            flash("Username already exists")
            return redirect(url_for("login"))

        new_id = max([u["id"] for u in users], default=0) + 1

        users.append({
            "id": new_id,
            "username": username,
            "full_name": request.form.get("full_name",""),
            "email": request.form.get("email",""),
            "phone": request.form.get("phone",""),
            "role": "user",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "password_hash": generate_password_hash(password)
        })

        write_json(USERS_FILE, users)

        session["user_id"] = new_id
        flash("Account created successfully")
        return redirect(url_for("home"))

    # -------- LOGIN --------
    elif action == "login":

        user = next((u for u in users if u["username"].lower()==username.lower()), None)

        if not user:
            flash("User not found")
            return redirect(url_for("login"))

        if not check_password_hash(user["password_hash"], password):
            flash("Wrong password")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        flash("Welcome back!")
        return redirect(url_for("home"))

    return redirect(url_for("login"))


# ===================== CART PAGES =====================
@app.route("/cart")
def cart():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    items, total = cart_items_detailed(user["id"])
    return render_template("cart.html", items=items, total=total)


# ===================== CART APIs =====================
@app.route("/api/cart/add", methods=["POST"])
def api_cart_add():
    user = current_user()
    if not user:
        return jsonify({"ok": False, "error": "login_required"}), 401

    data = request.get_json(force=True)
    pid = int(data.get("product_id"))
    qty = int(data.get("qty", 1))
    if qty < 1:
        qty = 1

    if not get_product(pid):
        return jsonify({"ok": False, "error": "invalid_product"}), 400

    cart = get_cart_for_user(user["id"])
    cart[str(pid)] = int(cart.get(str(pid), 0)) + qty
    save_cart_for_user(user["id"], cart)

    return jsonify({"ok": True, "cart_count": cart_count(user["id"])})


@app.route("/api/cart/update", methods=["POST"])
def api_cart_update():
    user = current_user()
    if not user:
        return jsonify({"ok": False, "error": "login_required"}), 401

    data = request.get_json(force=True)
    pid = int(data.get("product_id"))
    qty = int(data.get("qty", 1))

    cart = get_cart_for_user(user["id"])
    if qty <= 0:
        cart.pop(str(pid), None)
    else:
        cart[str(pid)] = qty

    save_cart_for_user(user["id"], cart)

    items, total = cart_items_detailed(user["id"])
    return jsonify({"ok": True, "cart_count": cart_count(user["id"]), "total": total, "items": items})


@app.route("/api/cart/remove", methods=["POST"])
def api_cart_remove():
    user = current_user()
    if not user:
        return jsonify({"ok": False, "error": "login_required"}), 401

    data = request.get_json(force=True)
    pid = int(data.get("product_id"))

    cart = get_cart_for_user(user["id"])
    cart.pop(str(pid), None)
    save_cart_for_user(user["id"], cart)

    items, total = cart_items_detailed(user["id"])
    return jsonify({"ok": True, "cart_count": cart_count(user["id"]), "total": total, "items": items})


# ===================== BUY NOW =====================
@app.route("/buy-now/<int:pid>")
def buy_now(pid):
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    if not get_product(pid):
        return "Product not found", 404

    session["buy_now"] = {"product_id": pid, "qty": 1}
    return redirect(url_for("checkout"))


# ===================== CHECKOUT =====================
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    buy_now_data = session.get("buy_now")

    if buy_now_data:
        pid = int(buy_now_data["product_id"])
        qty = int(buy_now_data["qty"])
        product = get_product(pid)

        if not product:
            session.pop("buy_now", None)
            return redirect(url_for("cart"))

        items = [{
            "id": pid,
            "name": product["name"],
            "price": int(product["price"]),
            "image": product.get("image", ""),
            "qty": qty,
            "line_total": qty * int(product["price"])
        }]
        total = items[0]["line_total"]
        mode = "buy_now"
    else:
        items, total = cart_items_detailed(user["id"])
        mode = "cart"

    if request.method == "GET":
        if not items:
            flash("Your cart is empty.")
            return redirect(url_for("cart"))
        return render_template("checkout.html", items=items, total=total, mode=mode)

    # POST: place order
    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()

    if not full_name or not phone or not address:
        flash("Please fill all fields.")
        return redirect(url_for("checkout"))

    orders = read_json(ORDERS_FILE, [])
    new_id = (max([o["order_id"] for o in orders]) + 1) if orders else 1

    order = {
    "order_id": new_id,
    "user_id": user["id"],
    "customer": {"full_name": full_name, "phone": phone, "address": address},
    "items": items,
    "total": total,
    "status": "Placed",
    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    orders.append(order)
    write_json(ORDERS_FILE, orders)

    # clear cart if this was cart checkout
    if buy_now_data:
        session.pop("buy_now", None)
    else:
        save_cart_for_user(user["id"], {})

    flash(f"Order placed successfully. Order #{new_id}")
    return redirect(url_for("orders"))

# ===================== update_order_status =====================
@app.route("/update_order_status/<int:oid>/<status>")
def update_order_status(oid, status):
    orders = read_json(ORDERS_FILE, [])

    valid = ["Placed","Confirmed","Packed","Shipped","Delivered"]
    if status not in valid:
        return "Invalid status"

    for o in orders:
        if o["order_id"] == oid:
            o["status"] = status
            break

    write_json(ORDERS_FILE, orders)
    return redirect(url_for("orders_page"))


# ===================== ORDERS =====================
@app.route("/orders")
def orders():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    orders = read_json(ORDERS_FILE, [])

    # 🔧 fix old orders without status
    for o in orders:
        if "status" not in o:
            o["status"] = "Placed"

    my_orders = [o for o in orders if o["user_id"] == user["id"]]
    my_orders.sort(key=lambda x: x["order_id"], reverse=True)

    return render_template("orders.html", orders=my_orders)

# ===================== RUN =====================
if __name__ == "__main__":
    ensure_files()
    app.run(debug=True)
