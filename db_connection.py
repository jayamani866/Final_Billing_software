import mysql.connector
from mysql.connector import Error

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="mani",
            password="Mani#2025",  # change to your real password
            database="billing_db"
        )
        return conn

    except Error as e:
        print("Connection Error:", e)
        return None
