from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from resources import api_blueprint
from config import Config
from database import db
from flask_cors import CORS
import time
from sqlalchemy.exc import OperationalError



app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

db.init_app(app)
jwt = JWTManager(app)

app.register_blueprint(api_blueprint)

if __name__ == '__main__':
    with app.app_context():
        for _ in range(10):
            try:
                db.create_all()
                print("bien la cosa")
                break
            except OperationalError:
                print("Database not ready yet. Retrying in 3 seconds...")
                time.sleep(3)

    app.run(host='0.0.0.0', port=5000, debug=True)

    