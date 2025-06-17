from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "admin_secret_key"

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

client = MongoClient("localhost", 27017)
db = client['ecommerce']
products = db.products

# Dummy login credentials
USERNAME = 'admin'
PASSWORD = 'admin123'

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['user'] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials!")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if 'user' not in session:
        return redirect(url_for("login"))
    all_products = list(products.find())  # ✅ Convert to list to avoid Jinja2 errors
    return render_template("index.html", products=all_products)

@app.route("/add", methods=["GET", "POST"])
def add_product():
    if 'user' not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        name = request.form['name']
        price = request.form['price']
        category = request.form['category']
        description = request.form['description']

        image_file = request.files['image']
        filename = secure_filename(image_file.filename)

        if filename:  # Only save if file was uploaded
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
        else:
            filename = 'default.png'

        products.insert_one({
            "name": name,
            "price": price,
            "category": category,
            "description": description,
            "image": filename
        })
        return redirect(url_for("dashboard"))
    return render_template("add_product.html")

@app.route("/edit/<id>", methods=["GET", "POST"])
def edit_product(id):
    if 'user' not in session:
        return redirect(url_for("login"))
    product = products.find_one({"_id": ObjectId(id)})
    if request.method == "POST":
        name = request.form['name']
        price = request.form['price']
        category = request.form['category']
        description = request.form['description']

        updated_data = {
            "name": name,
            "price": price,
            "category": category,
            "description": description
        }

        if 'image' in request.files and request.files['image'].filename != '':
            image_file = request.files['image']
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            updated_data['image'] = filename

        products.update_one({"_id": ObjectId(id)}, {"$set": updated_data})
        return redirect(url_for("dashboard"))
    return render_template("edit_product.html", product=product)

@app.route("/delete/<id>")
def delete_product(id):
    if 'user' not in session:
        return redirect(url_for("login"))
    products.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    # Add default image if not exists
    default_path = os.path.join(UPLOAD_FOLDER, 'default.png')
    if not os.path.exists(default_path):
        with open(default_path, 'wb') as f:
            f.write(b'')  # creates an empty placeholder PNG
    app.run(debug=True)
