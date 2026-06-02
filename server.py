from flask import Flask, request
from database import (
    create_or_get_user, update_user_vin, add_session, 
    add_wh, add_leaf_token, has_reward_today, add_reward,
    update_last_odo, get_last_odo
)
from datetime import date
import os

app = Flask(__name__)

@app.route('/update/', methods=['GET'])
def leafspy_update():
    token = request.args.get('user')
    # Ищем VIN и в заглавном, и в строчном варианте
    vin = request.args.get('VIN', request.args.get('vin', '')).upper()
    soh = request.args.get('soh', type=float)
    odo = request.args.get('odo', type=int)
    trip = request.args.get('trip', type=float, default=0)
    
    # Дополнительные параметры от LeafSpy
    bat_temp = request.args.get('BatTemp', type=float)
    soc = request.args.get('SOC', type=float)
    gids = request.args.get('Gids', type=int)
    amb_temp = request.args.get('Amb', type=float)
    latitude = request.args.get('Lat', type=float)
    longitude = request.args.get('Long', type=float)
    rpm = request.args.get('RPM', type=int)
    speed = request.args.get('Speed', type=float)
    bat_volts = request.args.get('BatVolts', type=float)
    bat_amps = request.args.get('BatAmps', type=float)
    quick_charges = request.args.get('QC', type=int)
    
    print(f"=== Запрос: token={token}, vin={vin}, odo={odo}")
    print(f"DEBUG: bat_temp={bat_temp}, soc={soc}, latitude={latitude}")
    
    if not token:
        return {"status": "error", "message": "Missing token"}
    
    user = create_or_get_user(token, vin if vin else None)
    user_id, db_vin, leaf_balance, wh_balance = user
    
    print(f"DEBUG: db_vin из БД = {db_vin}")
    print(f"DEBUG: vin из запроса = {vin}")
    print(f"DEBUG: условие (not db_vin and vin) = {not db_vin and vin}")
    
    if not db_vin and vin:
        print("DEBUG: Попытка привязать VIN")
        update_user_vin(token, vin)
        db_vin = vin
        print(f"DEBUG: VIN {vin} привязан")
    
    if db_vin and odo is not None:
        last_odo = get_last_odo(token)
        odo_diff = max(0, odo - last_odo)
        print(f"DEBUG: last_odo={last_odo}, odo_diff={odo_diff}")
        
        if odo_diff > 0:
            # Сохраняем сессию
            add_session(db_vin, soh, odo, trip, bat_temp, soc, gids, amb_temp, 
                        latitude, longitude, rpm, speed, bat_volts, bat_amps, quick_charges)
            print(f"Сохранена сессия для {db_vin}, пробег +{odo_diff} км")
            
            # Начисляем ёлки (1 км = 1 ёлка)
            add_wh(token, odo_diff)
            print(f"Начислено ёлок: {odo_diff}")
            
            # Обновляем last_odo
            update_last_odo(token, odo)
    
    # Начисление $LEAF (1 раз в день за поездку >=2 км)
    today = date.today().isoformat()
    if db_vin and odo is not None:
        last_odo = get_last_odo(token)
        odo_diff = max(0, odo - last_odo)
        if odo_diff >= 2 and not has_reward_today(db_vin, today):
            add_leaf_token(token)
            add_reward(db_vin, today)
            print(f"Начислен токен $LEAF")
    
    return {"status": "0"}

@app.route('/')
def home():
    return "Server is running"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
