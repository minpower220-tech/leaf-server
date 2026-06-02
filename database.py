import psycopg2
from datetime import datetime

# ЗАМЕНИ ЭТУ СТРОКУ НА ТВОЮ ИЗ SUPABASE!
DATABASE_URL = "postgresql://postgres.saulhayeumrjayidiyxd:ZMtm7M3tzUvH%2Ax%2F@aws-0-eu-north-1.pooler.supabase.com:5432/postgres"

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def create_or_get_user(api_token, vin=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT tg_id, vin, leaf_balance, wh_balance FROM users WHERE api_token = %s", (api_token,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (api_token, vin) VALUES (%s, %s) RETURNING tg_id, vin, leaf_balance, wh_balance", 
                  (api_token, vin))
        user = c.fetchone()
        print(f"Создан новый пользователь {api_token}")
    conn.commit()
    conn.close()
    return user

def update_user_vin(api_token, vin):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET vin = %s WHERE api_token = %s", (vin, api_token))
    conn.commit()
    conn.close()

def add_session(vin, soh, odo, trip):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO sessions (vin, soh, odo, trip_distance) VALUES (%s, %s, %s, %s)", 
              (vin, soh, odo, trip))
    conn.commit()
    conn.close()

def add_wh(api_token, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET wh_balance = wh_balance + %s WHERE api_token = %s", (amount, api_token))
    conn.commit()
    conn.close()

def add_leaf_token(api_token):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET leaf_balance = leaf_balance + 1 WHERE api_token = %s", (api_token,))
    conn.commit()
    conn.close()

def has_reward_today(vin, today):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM rewards WHERE vin = %s AND date = %s", (vin, today))
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def add_reward(vin, today):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO rewards (vin, date, amount) VALUES (%s, %s, 1)", (vin, today))
    conn.commit()
    conn.close()
