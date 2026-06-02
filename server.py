from flask import Flask, request
import sqlite3
from datetime import date
import re
import os

app = Flask(__name__)

@app.route('/update/', methods=['GET'])
def leafspy_update():
    # Получаем параметры от LeafSpy
    token = request.args.get('user')
    vin = request.args.get('vin', '').upper()
    soh = request.args.get('soh', type=float)
    odo = request.args.get('odo', type=int)
    trip = request.args.get('trip', type=float, default=0)
    
    print(f"=== Получен запрос ===")
    print(f"Токен: {token}")
    print(f"VIN: {vin}, SOH: {soh}, ODO: {odo}, TRIP: {trip}")
    
    if not token:
        print("Ошибка: нет токена")
        return {"status": "error", "message": "Missing token"}
    
    # Подключаемся к базе
    conn = sqlite3.connect('leaf.db')
    c = conn.cursor()
    
    # Создаём таблицы
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
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
    
    # Проверяем токен
    c.execute("SELECT tg_id, vin, leaf_balance, wh_balance FROM users WHERE api_token = ?", (token,))
    user = c.fetchone()
    
    if not user:
        print(f"Ошибка: токен {token} не найден в базе")
        conn.close()
        return {"status": "error", "message": "Invalid token"}
    
    tg_id, db_vin, leaf_balance, wh_balance = user
    print(f"Найден пользователь tg_id={tg_id}, текущий VIN={db_vin}")
    
    # Привязываем VIN
    if not db_vin and vin:
        c.execute("UPDATE users SET vin = ? WHERE api_token = ?", (vin, token))
        db_vin = vin
        print(f"Привязан VIN {vin}")
    
    # Сохраняем поездку
    if db_vin and trip and trip > 0:
        c.execute('''INSERT INTO sessions (vin, soh, odo, trip_distance, recorded_at)
                     VALUES (?, ?, ?, ?, datetime('now'))''',
                  (db_vin, soh, odo, trip))
        print(f"Сохранена поездка: {trip} км")
        
        wh_earned = int(trip)
        c.execute("UPDATE users SET wh_balance = wh_balance + ? WHERE api_token = ?",
                  (wh_earned, token))
        print(f"Начислено Wh: {wh_earned}")
    
    # Начисляем токен
    today = date.today().isoformat()
    if db_vin:
        c.execute("SELECT COUNT(*) FROM rewards WHERE vin = ? AND date = ?", (db_vin, today))
        already_rewarded = c.fetchone()[0] > 0
        
        if not already_rewarded and trip and trip >= 2:
            c.execute("UPDATE users SET leaf_balance = leaf_balance + 1 WHERE api_token = ?", (token,))
            c.execute("INSERT INTO rewards (vin, date, amount) VALUES (?, ?, 1)", (db_vin, today))
            print(f"Начислен токен $LEAF (сегодня впервые)")
        else:
            print(f"Токен сегодня уже начислен (already_rewarded={already_rewarded}) или поездка короткая ({trip} км)")
    
    conn.commit()
    conn.close()
    print("Ответ: статус 0")
    return {"status": "0"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Запуск сервера на порту {port}...")
    print(f"Локальный адрес: http://localhost:{port}")
    print(f"Жду запросы от LeafSpy...")
    app.run(host='0.0.0.0', port=port, debug=True)