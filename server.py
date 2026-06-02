from flask import Flask, request
from database import (
    create_or_get_user, update_user_vin, add_session, 
    add_wh, add_leaf_token, has_reward_today, add_reward
)
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
    
    user = create_or_get_user(token, vin if vin else None)
    tg_id, db_vin, leaf_balance, wh_balance = user
    
    if not db_vin and vin:
        update_user_vin(token, vin)
        db_vin = vin
        print(f"Привязан VIN {vin}")
    
    if db_vin and trip and trip > 0:
        add_session(db_vin, soh, odo, trip)
        print(f"Сохранена поездка: {trip} км")
        add_wh(token, int(trip))
        print(f"Начислено Wh: {int(trip)}")
    
    today = date.today().isoformat()
    if db_vin and trip and trip >= 2:
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
