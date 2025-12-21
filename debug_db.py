import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_PASSWORD")
database = os.getenv("MYSQL_DATABASE")

hosts_to_test = [
    "69.72.248.158",
    "addishomess.com",
    "s10156.lon1.stableserver.net"
]

print(f"Testing connections for user: {user}")
print("-" * 50)

for host in hosts_to_test:
    print(f"\n[TESTING] Host: {host}")
    try:
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=3306,
            connect_timeout=10
        )
        print(f"✅ SUCCESS: Connected to {host}!")
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"   Server version: {version}")
        conn.close()
        # If one works, we can stop or just let the user know all of them
    except Exception as e:
        error_code = getattr(e, 'args', [None])[0]
        error_msg = getattr(e, 'args', [None, ""])[1]
        print(f"❌ FAILURE on {host}: Error {error_code} - {error_msg}")
