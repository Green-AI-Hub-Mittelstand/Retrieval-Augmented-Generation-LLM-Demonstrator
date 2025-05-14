from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)
socketio = SocketIO(app)
CORS(app)

@app.route('/')
def index():
    return "SocketIO Test"

if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0", port=5001)