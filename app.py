from flask import Flask, render_template, request, redirect, session
import json
from ai.recommender import recommend

app = Flask(__name__)
app.secret_key = "cartiq_secret"


# ---------- Helpers ----------

def load_json(file):
    with open(file) as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)


def log_activity(user, product_id, action):
    data = load_json("activity.json")
    data.append({
        "user": user,
        "product_id": product_id,
        "action": action
    })
    save_json("activity.json", data)


# ---------- Routes ----------

@app.route("/")
def home():
    products = load_json("products.json")

    recommendations = []
    if "user" in session:
        activity = load_json("activity.json")
        user_views = [a for a in activity if a["user"] == session["user"]]

        if user_views:
            last_product = user_views[-1]["product_id"]
            recommendations = recommend(last_product)

    return render_template(
        "index.html",
        products=products,
        recommendations=recommendations
    )


@app.route("/product/<int:id>")
def product(id):
    products = load_json("products.json")
    product = next(p for p in products if p["id"] == id)

    if "user" in session:
        log_activity(session["user"], id, "view")

    recs = recommend(id)

    return render_template("product.html", product=product, recs=recs)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]

        users = load_json("users.json")

        if username not in users:
            users.append(username)
            save_json("users.json", users)

        session["user"] = username
        return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
