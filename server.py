from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/update/', methods=['GET'])
def leafspy_update():
    token = request.args.get('user')
    print(f"Запрос принят с токеном: {token}")
    return {"status": "0"}

@app.route('/')
def home():
    return "Server is running"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
