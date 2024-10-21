from flask import request
from config import get_db_connection
from datetime import datetime
def get_user_id_by_email(email):
    if not email:
        return None  
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT user_id FROM user WHERE email = %s", (email,))
        result = cursor.fetchone()
        if result:
            return result[0] 
        else:
            return None 
    except Exception as e:
        print(f"Error: {e}")
        return None  
    finally:
        connection.close()

def  have_bank_account(mail):
    user_id=get_user_id_by_email(mail)
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM bank_account WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    if result[0] > 0:
      return True
    else:
     return False
    # total amount
def total_amount(email):
    user_id = get_user_id_by_email(email)
    if not user_id:
        return None
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT SUM(balance) FROM bank_account WHERE user_id = %s", (user_id,))
        total_balance = cursor.fetchone()[0]  
        if total_balance is None:
            total_balance = 0 
        return total_balance
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        connection.close()
#  get name and current amount as a dict
def get_bank_names_and_balances(email):
    user_id = get_user_id_by_email(email)
    if not user_id:
        return None
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT acc_name, balance,acc_id 
            FROM bank_account
            WHERE user_id = %s
        """, (user_id,))
        bank_details = cursor.fetchall()
        if bank_details:
            return bank_details
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        connection.close()

def account_id(email):
    user_id=get_user_id_by_email(email)
    if not user_id:
        return None  
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT acc_id FROM bank_account WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            acc_id = result[0]  
            return acc_id
        else:
            return None  
    except Exception as e:
        print(f"Error: {e}")
        return None  
    finally:
        connection.close()  

def get_transition_id(account_id):
    if not account_id:
        return None 
    connection = get_db_connection()  
    cursor = connection.cursor() 
    try:
        cursor.execute("SELECT t_id FROM transactions WHERE acc_id = %s", (account_id,))
        result = cursor.fetchone() 
        if result:
            t_id = result[0] 
            return t_id
        else:
            return None 
    except Exception as e:
        print(f"Error: {e}")
        return None  
    finally:
        connection.close()

# expense of user
def get_expense_sum(email):
    user_id=get_user_id_by_email(email)
    if not user_id:
        return None
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT SUM(e.amount) AS total_expense
            FROM expense e
            JOIN transactions t ON e.t_id = t.t_id
            JOIN bank_account ba ON t.acc_id = ba.acc_id
            WHERE ba.user_id = %s
        """, (user_id,))
        
        expense_details = cursor.fetchone()
        if expense_details and expense_details['total_expense'] is not None:
            return expense_details['total_expense']
        else:
            return 0.0 
    
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    finally:
        connection.close()

# income of user
def get_income_sum(email):
    user_id=get_user_id_by_email(email)
    if not user_id:
        return None  
    connection = get_db_connection() 
    cursor = connection.cursor(dictionary=True) 
    
    try:
        cursor.execute("""
            SELECT SUM(i.amount) AS total_income
            FROM income i
            JOIN transactions t ON i.t_id = t.t_id
            JOIN bank_account ba ON t.acc_id = ba.acc_id
            WHERE ba.user_id = %s
        """, (user_id,))
        
        income_details = cursor.fetchone()
        if income_details and income_details['total_income'] is not None:
            return income_details['total_income']
        else:
            return 0.0
    
    except Exception as e:
        print(f"Error: {e}")
        return None  
    
    finally:
        connection.close()


def add_transaction(amount, transaction_type, acc_id, transition_id,description="None"):
    connection = get_db_connection()
    cursor = connection.cursor()
    current_date = datetime.now()

    insert_query = """
    INSERT INTO transactions (t_id, amount, date, type, acc_id, description)
    VALUES (%s, %s, %s, %s, %s ,%s)
    """
    try:
        cursor.execute(insert_query, (transition_id, amount, current_date, transaction_type, acc_id,description))
        connection.commit()
        print("Transaction added and balance updated successfully.")
    except Exception as e:
        print(f"Error: {e}")
        connection.rollback() 
    finally:
        cursor.close()
        connection.close()
def get_transactions(email):
    connection = get_db_connection() 
    cursor = connection.cursor()
    user_id = get_user_id_by_email(email)
    if user_id is None:
        print("User not found.")
        return []
    
    query = """
    SELECT t_id, amount, date, type, acc_id, description 
    FROM transactions 
    WHERE acc_id IN (
        SELECT acc_id FROM bank_account WHERE user_id = %s
    )
    ORDER BY date DESC
    """
    
    try:
        cursor.execute(query, (user_id,))
        transactions = cursor.fetchall() 
        transaction_list = []
        for i, transaction in enumerate(transactions):
            transaction_list.append({
                's_no': i + 1,
                't_id': transaction[0],     
                'amount': transaction[1],   
                'date': transaction[2],   
                'type': transaction[3],     
                'acc_id': transaction[4],
                'description': transaction[5] 
            })
        return transaction_list
    finally:
        cursor.close()
        connection.close()


def add_income(transaction_id, amount, description, income_type="Income"):
    connection = get_db_connection()
    cursor = connection.cursor()
    current_date = datetime.now().date()
    current_time = datetime.now().time()
    insert_income_query = """
    INSERT INTO income (t_id, amount, description, type, date,time)
    VALUES (%s, %s, %s, %s, %s,%s)
    """
    update_balance_query = """
    UPDATE bank_account 
    SET balance = balance + %s
    WHERE acc_id = (SELECT acc_id FROM transactions WHERE t_id = %s)
    """
    try:
        cursor.execute(insert_income_query, (transaction_id, amount, description, income_type, current_date,current_time))
        cursor.execute(update_balance_query, (amount, transaction_id))
        connection.commit()
        print("Income added successfully.")
    except Exception as e:
        print(f"Error: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

def add_expense(transaction_id, amount, description, expense_type="Expense"):
    connection = get_db_connection()
    cursor = connection.cursor()
    current_date = datetime.now().date()
    current_time = datetime.now().time() 
    insert_expense_query = """
    INSERT INTO expense (t_id, amount, date, time, type, remarks)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    update_balance_query = """
    UPDATE bank_account 
    SET balance = balance - %s
    WHERE acc_id = (SELECT acc_id FROM transactions WHERE t_id = %s)
    """
    try:
        cursor.execute(insert_expense_query, (transaction_id, amount, current_date, current_time, expense_type, description))
        cursor.execute(update_balance_query, (amount, transaction_id))
        connection.commit()
        print("Expense added successfully.")
    
    except Exception as e:
        print(f"Error: {e}")
        connection.rollback()
    
    finally:
        cursor.close()
        connection.close()

def is_transaction_present(transaction_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
    SELECT COUNT(*) 
    FROM transactions 
    WHERE t_id = %s
    """
    try:
        cursor.execute(query, (transaction_id,))
        result = cursor.fetchone()  
        return result[0] > 0 
    finally:
        cursor.close()
        connection.close()



# to delete and uptodate
def delete_income(t_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM income WHERE t_id = %s", (t_id,))
    connection.commit()
    connection.close()

def delete_expense(t_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM expense WHERE t_id = %s", (t_id,))
    connection.commit()
    connection.close()

def delete_transaction(t_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM transactions WHERE t_id = %s", (t_id,))
    connection.commit()
    connection.close()

def get_bank_by_id(acc_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM bank_account WHERE acc_id = %s", (acc_id,))
        bank = cursor.fetchone()
        
        if bank:
            return bank  
        else:
            return None  
    finally:
        cursor.close()
        connection.close()

def get_bank_by_id(acc_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT acc_id, acc_name, balance 
            FROM bank_account
            WHERE acc_id = %s
        """, (acc_id,))
        bank_details = cursor.fetchone()  
        if bank_details:
            return bank_details
        else:
            return None  
    except Exception as e:
        print(f"Error: {e}")
        return None  
    finally:
        connection.close()

def update_bank_balance(acc_id, amount, transaction_type):
    connection = get_db_connection() 
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT balance FROM bank_account WHERE acc_id = %s", (acc_id,))
        result = cursor.fetchone()
        if result is None:
            print("Account not found.")
        current_balance = result[0]
        if transaction_type == 'income':
            new_balance = float(current_balance) + float(amount)
        else:
            new_balance = float(current_balance) - float(amount)

        cursor.execute(
            "UPDATE bank_account SET balance = %s WHERE acc_id = %s",
            (new_balance, acc_id)
        )
        connection.commit()
        print("Bank balance updated successfully.")
    finally:
        cursor.close()
        connection.close()

def is_balance_higher(acc_id, amount):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT balance FROM bank_account WHERE acc_id = %s"
    cursor.execute(query, (acc_id,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    if result is None:
        return False
    balance = result['balance']
    return balance >= amount
