from database import db

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    items = db.relationship('Item', backref='store', lazy=True, cascade="all, delete")

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    role_settings = db.relationship('UserRoleSettings', backref='user', uselist=False, cascade='all, delete-orphan')

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.role_settings = UserRoleSettings(isSeller=False)

class UserRoleSettings(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    isSeller = db.Column(db.Boolean, default=False )
    address = db.Column(db.String(255))