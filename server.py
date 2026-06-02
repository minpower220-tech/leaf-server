from flask import Flask, request
import sqlite3
from datetime import date
import os

app = Flask(__name__)

@app.route('/update/', methods=['GET'])
def leafspy_update():
    token = request.args.get('user')
    vin = request.args.get('vin', '').upper()
    soh = request.args.get('soh', type=float)
    odo = request.args.get('odo', type=int)
    trip = request.args.get('trip', type=float, default=0)
    
    print(f"=== Запрос: token={token}, vin={vin}, trip={trip}")
    
    if not token:
        return {"status": "error", "message": "Missing token"}
    
    db_path = '/tmp/leaf.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Создаём таблицы
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_token TEXT UNIQUE NOT NULL,
            vin TEXT,
            leaf_balance INTEGER DEFAULT 0,
            wh_balance INTEGER DEFAULT 0,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vin TEXT NOT NULL,
            soh REAL,
            odo INTEGER,
            trip_distance REAL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            vin TEXT NOT NULL,
            date TEXT NOT NULL,
            amount INTEGER DEFAULT 1,
            PRIMARY KEY (vin, date)
        )
    ''')
    
    # Находим или создаём пользователя
    c.execute("SELECT vin, leaf_balance, wh_balance FROM users WHERE api_token = ?", (token,))
    user = c.fetchone()
    
    if not user:
        c.execute("INSERT INTO users (api_token, vin) VALUES (?, ?)", (token, vin if vin else None))
        c.execute("SELECT vin, leaf_balance, wh_balance FROM users WHERE api_token = ?", (token,))
        user = c.fetchone()
        print(f"Создан новый пользователь с токеном {token}")
    
    db_vin, leaf_balance, wh_balance = user
    
    if not db_vin and vin:
        c.execute("UPDATE users SET vin = ? WHERE api_token = ?", (vin, token))
        db_vin = vin
        print(f"Привязан VIN {vin}")
    
    if db_vin and trip and trip > 0:
        c.execute('''INSERT INTO sessions (vin, soh, odo, trip_distance, recorded_at)
                     VALUES (?, ?, ?, ?, datetime('now'))''',
                  (db_vin, soh, odo, trip))
        print(f"Сохранена поездка: {trip} км")
        
        wh_earned = int(trip)
        c.execute("UPDATE users SET wh_balance = wh_balance + ? WHERE api_token = ?", (wh_earned, token))
        print(f"Начислено Wh: {wh_earned}")
    
    if db_vin and trip and trip >= 2:
        today = date.today().isoformat()
        c.execute("SELECT COUNT(*) FROM rewards WHERE vin = ? AND date = ?", (db_vin, today))
        already_rewarded = c.fetchone()[0] > 0
        
        if not already_rewarded:
            c.execute("UPDATE users SET leaf_balance = leaf_balance + 1 WHERE api_token = ?", (token,))
            c.execute("INSERT INTO rewards (vin, date, amount) VALUES (?, ?, 1)", (db_vin, today))
            print(f"Начислен токен $LEAF")
    
    conn.commit()
    conn.close()
    return {"status": "0"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
