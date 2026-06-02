import psycopg2
from datetime import datetime

DATABASE_URL = "postgresql://postgres.saulhayeumrjayidiyxd:LeafToken2025Project@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def create_or_get_user(api_token, vin=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, vin, leaf_balance, wh_balance FROM users WHERE api_token = %s", (api_token,))
    user = c.fetchone()

    if not user:
        c.execute("INSERT INTO users (api_token, vin) VALUES (%s, %s) RETURNING id, vin, leaf_balance, wh_balance",
                  (api_token, vin))
        user = c.fetchone()
        print(f"Создан новый пользователь с токеном {api_token}")
    conn.commit()
    conn.close()
    return user

def update_user_vin(api_token, vin):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET vin = %s WHERE api_token = %s", (vin, api_token))
    conn.commit()
    conn.close()

def update_last_odo(api_token, odo):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET last_odo = %s WHERE api_token = %s", (odo, api_token))
    conn.commit()
    conn.close()

def get_last_odo(api_token):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT last_odo FROM users WHERE api_token = %s", (api_token,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def add_session(vin, soh, odo, trip, bat_temp, soc, gids, amb_temp, latitude, longitude, rpm, speed, bat_volts, bat_amps, quick_charges):
    print(f"DEBUG add_session: vin={vin}, soh={soh}, odo={odo}, trip={trip}")
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO sessions (
                vin, soh, odo, trip_distance, 
                bat_temp, soc, gids, amb_temp, 
                latitude, longitude, rpm, speed, 
                bat_volts, bat_amps, quick_charges
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (vin, soh, odo, trip, bat_temp, soc, gids, amb_temp, latitude, longitude, rpm, speed, bat_volts, bat_amps, quick_charges))
        conn.commit()
        print("DEBUG add_session: INSERT успешен")
    except Exception as e:
        print(f"DEBUG add_session: ОШИБКА - {e}")
    finally:
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
