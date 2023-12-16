import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd
import sqlite3
import io
import base64
import matplotlib.pyplot as plt
import numpy as np
from flask import jsonify


#Configure application
app = Flask(__name__, static_folder='static')


app.secret_key = os.environ.get("MySuperSecretKey123!@#")
#Custom filter
app.jinja_env.filters["usd"] = usd

#Configure session to use filesystem (instead of signed cookies)
app.config["SESSION PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#Configure CS%) Library to use database SQLITE database

db = SQL("sqlite:///expense.db")

@app.after_request
def after_request(response):
    """Ensure responses are not cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/about", methods=["GET", "POST"])
@login_required
def about():
    if request.method == "POST":
        return redirect("/about")

    return render_template("about.html")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/homepage", methods=["GET", "POST"])
@login_required
def homepage():
    if request.method == "POST":
        return redirect("/homepage")

    return render_template("homepage.html")

@app.route("/main")
@login_required
def main():

    username = db.execute("SELECT username FROM users WHERE user_id = ?", (session["user_id"]))

    # Fetch savings for the user from the savings table
    savings = db.execute("SELECT amount FROM savings WHERE user_id = ?", (session["user_id"]))

    # Fetch income for the user from the income table
    income = db.execute("SELECT * FROM income WHERE user_id = ?", (session["user_id"]))

    expenses = db.execute("SELECT amount FROM expense WHERE user_id = ?", (session["user_id"]))


    # Calculate the totals
    total_expense = sum(expense["amount"] if expense["amount"] is not None else 0 for expense in expenses)
    total_income = sum(income["amount"] if income["amount"] is not None else 0 for income in income)
    total_savings = sum(savings["amount"] if savings["amount"] is not None else 0 for savings in savings)


    # Calculate the remaining income
    remaining_income = total_income - total_expense - total_savings

    return render_template("main.html", username=username, savings=savings, expenses=expenses, total_savings=total_savings, income=income, total_income=total_income, total_expense=total_expense, remaining_income=remaining_income)
@app.route("/history")
@login_required
def history():
    user_id = session["user_id"]  # Make sure you're retrieving the user_id properly
    expenses = db.execute(
       "SELECT id, category, amount, timestamp FROM expense WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))

    savings = db.execute("SELECT id, amount, timestamp FROM savings WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))

    return render_template("history.html", expenses=expenses, savings=savings, user_id=user_id)

@app.route('/get_expense/<int:user_id>', methods=['POST'])
def get_expense(user_id):
    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, category, amount, timestamp FROM expense WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    expense = cursor.fetchall()

    conn.close()

    return jsonify({"expense": expense}), 200


@app.route('/delete_expense/<int:user_id>/<int:expense_id>', methods=['DELETE'])
def delete_expense(user_id, expense_id):
    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()

    try:
        # Delete the expense associated with the provided expense_id and user_id
        cursor.execute("DELETE FROM expense WHERE id=? AND user_id=?", (expense_id, user_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Expense deleted successfully"}), 200
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"message": f"Error deleting expense: {str(e)}"}), 500

@app.route('/get_savings/<int:user_id>', methods=['GET'])
def get_savings(user_id):
    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, amount, timestamp FROM savings WHERE user_id=? ORDER BY timestamp DESC", (user_id,))
    savings = cursor.fetchall()

    conn.close()

    return jsonify({"savings": savings}), 200

@app.route('/delete_savings/<int:user_id>/<int:savings_id>', methods=['DELETE'])
def delete_savings(user_id, savings_id):
    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM savings WHERE id=? AND user_id=?", (savings_id, user_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Savings deleted successfully"}), 200
    except Exception as e:
            conn.rollback()
            conn.close()
            return jsonify({"message": f"Error deleting saving: {str(e)}"}), 500


@app.route("/Addincome", methods=["GET", "POST"])
@login_required
def Addincome():
    if request.method == "POST":
        amount = request.form.get("amount")

        if not amount or not amount.isdigit():
            return apology("Invalid income")

        amount = int(amount)

        # Update income for user_id in the database
        db.execute("INSERT INTO income (user_id, amount) VALUES (?, ?)", session["user_id"], amount)


        flash(f"Added income: {usd(amount)}!", "header1")
        flash(f"Congrats on the raise! Remember to budget wisely and save for the future.", "header2")
        return redirect("/main")
    else:
        return render_template("Addincome.html")

@app.route("/Addexpense", methods=["GET", "POST"])
@login_required
def Addexpense():
    if request.method == "POST":
        amount = request.form.get("amount")
        category = request.form.get("category")

        print(f"expense: {amount}")
        print(f"category: {category}")

        if not amount or not amount.isdigit():
            return apology("Invalid expense")

        # Convert amount to an integer
        amount = int(amount)

        # Insert the expense into the expenses table
        db.execute("INSERT INTO expense (user_id, category, amount) VALUES (?, ?, ?)",
                   session["user_id"],
                   category,
                   amount)

        flash(f"Added {usd(amount)} for Category {category}!", "header1")
        flash(f"You have been spending a lot. Consider budgeting and cutting down on unnecessary expenses", "header2")
        return redirect("/main")
    else:
        # Get the user's total expense

        return render_template("Addexpense.html")


@app.route("/savings", methods=["GET", "POST"])
@login_required
def savings():
    if request.method == "POST":
        amount = request.form.get("amount")

        if not amount or not amount.isdigit():
            return apology("Invalid savings")

        print(f"Savings: {savings}")

        db.execute("INSERT INTO savings (user_id, amount) VALUES (?, ?)", session["user_id"], amount)

        flash(f"Added {usd(amount)} to your savings!", "header1")
        flash(f"Congratulations! You have savings. Keep up the good work!", "header2")

        return redirect("/main")
    else:
        return render_template("savings.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()

    #User reached route via POST for form submission
    if request.method == "POST":

        #Ensure username was submitted
        username = request.form.get("username")
        if not username:
            return apology("must provide username", 400)
        #Ensure password was submitted
        password = request.form.get("password")
        if not password:
            return apology("must provide password", 400)

        #Ensure password confirmation was submitted
        password_confirmation = request.form.get("password_confirmation")
        if not password_confirmation:
            return apology("must confirm password", 400)

        #Check if both passwords match
        if password != password_confirmation:
            return apology("passwords do not match", 400)

        #Check if username is already taken
        existing_user = db.execute("SELECT * FROM users WHERE username = ?", username)
        if existing_user:
            return apology("username already taken")

        #Hash the password
        hashed_password = generate_password_hash(password)

        #Insert new user into database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hashed_password)

        #Redirect user to login page
        return redirect("/login")

    #User reached via GET method
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Log user in
    session.clear()
    # User reached route via POST method
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username and password are correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged In
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to index page
        return redirect("/homepage")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():

    #Log user out

    session.clear()

    return redirect("/")

def fetch_expenses(user_id):
    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT category, SUM(amount) FROM expense WHERE user_id = ? GROUP BY category",
        (user_id,),
    )
    expenses = cursor.fetchall()

    conn.close()

    categorized_expenses = {
        "Food": 0,
        "Grocery": 0,
        "Bills": 0,
        "Fuel": 0,
        "Others": 0,
    }

    for category, amount in expenses:
        categorized_expenses[category] = amount

    return categorized_expenses

@app.route("/chart", methods=["GET", "POST"])
@login_required
def chart():
    if request.method == "POST":
        user_id = session.get("user_id")
        if user_id is None:
            return "User not authenticated", 403

        chart_data = fetch_expenses(user_id)
        return jsonify(chart_data)

    return render_template("chart.html")



def get_monthly_savings(user_id):
    conn = sqlite3.connect("expense.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT strftime('%Y-%m', timestamp) AS month,
            SUM(amount) AS total_amount
        FROM savings
        WHERE user_id = ?
        GROUP BY month
        ORDER BY month ASC
    """, (user_id,))



    rows = cursor.fetchall()
    data = {row[0]: row[1] for row in rows}

    conn.close()
    return data

@app.route("/charts", methods=["GET", "POST"])
@login_required
def charts():
    if request.method == "POST":
        user_id = session.get("user_id")
        if user_id is None:
            return "User not authenticated", 403

        chart_data = get_monthly_savings(user_id)
        return jsonify(chart_data)

    return render_template("chart.html")


