from flask import Flask, render_template, request, redirect, url_for, session
import bcrypt
from config import get_db_connection
import models 
import random
from flask import  flash

app = Flask(__name__)
app.secret_key = 'secret_key'
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

@app.route('/')
def introduction():
    return render_template('introduction.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        
        hashed_password = hash_password(password)
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO user (Name, Email, Phone, Password)
                VALUES (%s, %s, %s, %s)
            """, (name, email, phone, hashed_password))
            connection.commit()
        except Exception as e:
            connection.rollback()
            return f"Error: {e}"
        finally:
            connection.close()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        user = cursor.fetchone()
        connection.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['email'] = email
            if models.have_bank_account(email):
                return redirect(url_for('index'))
            else:
             return redirect(url_for('add_bank'))
        else:
            return "Login failed. Invalid email or password."
    return render_template('login.html')

@app.route('/add_bank', methods=['GET', 'POST'])
def add_bank():
    if request.method == 'POST':
        acc_name = request.form['acc_name']
        acc_type = request.form['type']
        acc_number = request.form['acc_number']
        balance = request.form['balance']
        description = request.form['description']
        email = session.get('email')
        if not email:
            return redirect(url_for('login'))
        user_id = models.get_user_id_by_email(email)
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO bank_account (user_id, acc_name, type, acc_number, balance, description)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, acc_name, acc_type, acc_number, balance, description))
            connection.commit()
            return redirect(url_for('index'))
        except Exception as e:
            connection.rollback()
            print(f"Error: {e}")
            return "An error occurred while adding the bank account."
        finally:
            connection.close()
    return render_template('add_bank.html')




@app.route('/index', methods=['GET', 'POST'])
def index():
    # to add data
    email = session.get('email')
    if not email:
        return redirect(url_for('login'))
    if request.method == 'POST':
        bank_id = int(request.form.get('bank_id'))
        transaction_type = request.form.get('type')
        amount =float( request.form.get('amount'))
        description = request.form.get('description')
        transaction_id =random.randint(1,100000)
        while(models.is_transaction_present(transaction_id=transaction_id)):
            transaction_id =random.randint(1,100000)
        
        if not bank_id or not transaction_type or not amount or not transaction_id:
            return redirect(url_for('index'))
        try:
            amount = float(amount)  
            transaction_id = int(transaction_id)  
            if transaction_type not in ["Income", "Expense"]:
                return redirect(url_for('index'))
            if transaction_type == 'Income':
                models.add_transaction(amount, "Income", bank_id, transaction_id,description)
                models.add_income(transaction_id, amount, description,"Income")
            else:
                if(models.is_balance_higher(bank_id,amount)):
                   models.add_transaction(amount, "Expense", bank_id, transaction_id,description)
                   models.add_expense(transaction_id, amount, description,"Expense")
                else:
                    return redirect(url_for('index'))
        except Exception as e:
            return redirect(url_for('index'))
        return redirect(url_for('index'))
# to add data
# to retrive data
    total_balance = models.total_amount(email)
    total_income = models.get_income_sum(email)
    total_expense = models.get_expense_sum(email)
    bank_details = models.get_bank_names_and_balances(email)
    transactions = models.get_transactions(email)
    return render_template('index.html', 
                           total_balance=total_balance, 
                           total_income=total_income, 
                           total_expense=total_expense,
                           bank_details=bank_details,
                           transactions=transactions)
@app.route('/delete_transaction/<int:t_id>/<string:transaction_type>/<int:acc_id>/<float:amount>', methods=['POST', 'GET'])
def delete_transaction(t_id, transaction_type, acc_id, amount):
        if transaction_type.lower() == "income":
            models.delete_income(t_id)
            models.update_bank_balance(acc_id,amount,"income")
        else:
            models.delete_expense(t_id)  
            models.update_bank_balance(acc_id,amount,"expense")
        models.delete_transaction(t_id)
        return redirect(url_for('index'))


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))
if __name__ == '__main__':
    app.run(debug=True)
