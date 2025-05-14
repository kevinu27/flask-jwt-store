## Para levantar lo normal sin docker
Opcional ( yo no lo usé)

python -m venv venv  # Create a virtual environment
source venv/bin/activate  # Activate (on macOS/Linux)
venv\Scripts\activate  # Activate (on Windows)

2
pip install -r requirements.txt
pip install flask flask_sqlalchemy flask_jwt_extended werkzeug


3
set JWT_SECRET_KEY=myjwtsecret

4
python

from app import db, app

with app.app_context():
    db.create_all()
print("Database tables created successfully!")

5
python app.py



## Para levantarlo con DOCKER:
1
pip install -r requirements.txt

2
docker build -t flask-api .

3
docker run -p 5000:5000 flask-api


## base de datos con docker
1 el dockerfile de la base de datos:

FROM mysql:8.0

ENV MYSQL_ROOT_PASSWORD=rootpassword
ENV MYSQL_DATABASE=midb
ENV MYSQL_USER=usuario
ENV MYSQL_PASSWORD=contrasena

EXPOSE 3306

2
 docker build -t mi-mysql . 
 o
 docker run --name some-mysql -v /my/own/datadir:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=admin -d mi-mysql

 3

