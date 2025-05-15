import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
    'DATABASE_URI',
    'mysql+pymysql://root:rootpassword@localhost:3306/midb'
)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'myjwtsecret')
