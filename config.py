# import os

# class Config:
#     SQLALCHEMY_DATABASE_URI = 'sqlite:///data.db'
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'myjwtsecret')

# import os

# class Config:
#     SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql://user:password@db:5432/mydatabase')
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'myjwtsecret')


import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
    'DATABASE_URI',
    'mysql+pymysql://root:rootpassword@db:3306/midb'
)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'myjwtsecret')
