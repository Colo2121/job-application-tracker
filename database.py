import mysql.connector
from mysql.connector import Error


def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="root",
        database="job_tracker",
        connection_timeout=5,
        use_pure=True
    )


def test_connection():
    try:
        conn = get_db_connection()
        if conn.is_connected():
            version = conn.get_server_info()
            conn.close()
            return True, f"Connected to MySQL Server version {version}"
        return False, "Connection failed."
    except Error as e:
        return False, str(e)


# Optional test block (safe)
if __name__ == "__main__":
    print("Testing database connection...")
    ok, msg = test_connection()
    print("OK:", ok)
    print("MESSAGE:", msg)