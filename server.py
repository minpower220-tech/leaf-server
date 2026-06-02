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
    vin = request.args.get('VIN', request.args.get('vin', '')).upper()
    soh = request.args.get('soh', type=float)
    odo = request.args.get('odo', type=int)
    trip = request.args.get('trip', type=float, default=0)
    
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
    
    print(f"=== Запрос: token={token}, vin={vin}, odo={odo}, trip={trip}")
    
    if not token:
        return {"status": "error", "message": "Missing token"}
    
    user = create_or_get_user(token, vin if vin else None)
    user_id, db_vin, leaf_balance, wh_balance = user
    
    if not db_vin and vin:
        update_user_vin(token, vin)
        db_vin = vin
        print(f"Привязан VIN {vin}")
    
    # СОХРАНЯЕМ ВСЕ ЗАПРОСЫ (без условий)
    if db_vin:
        add_session(db_vin, soh, odo, trip, bat_temp, soc, gids, amb_temp, 
                    latitude, longitude, rpm, speed, bat_volts, bat_amps, quick_charges)
        print(f"Сохранена сессия для {db_vin}, odo={odo}, trip={trip}")
        
        # Начисление ёлок (только если пробег увеличился)
        if odo is not None:
            last_odo = get_last_odo(token)
            odo_diff = max(0, odo - last_odo)
            if odo_diff > 0:
                add_wh(token, odo_diff)
                print(f"Начислено ёлок: {odo_diff}")
                update_last_odo(token, odo)
    
    # Начисление $LEAF (1 раз в день, если поездка была)
    today = date.today().isoformat()
    if db_vin and trip >= 2:
        if not has_reward_today(db_vin, today):
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
