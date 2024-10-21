import mysql.connector
def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='AMIT@123',
        database='finance_tracker'
    )
    return connection
