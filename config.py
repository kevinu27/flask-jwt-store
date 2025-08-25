import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
    'DATABASE_URI',
    'mysql+pymysql://root:rootpassword@localhost:3306/midb'
    # 'mysql+pymysql://root:rootpassword@host.docker.internal:3306/midb'  - se descomentaria esta linea y se comentaria la de arriba cuando labasede de datos y el backend esten ambos dockerizados
)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'myjwtsecret')
