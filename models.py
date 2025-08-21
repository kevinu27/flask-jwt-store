from database import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    items = db.relationship('Item', backref='store', lazy=True, cascade="all, delete")
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    # Add image relationship
    images = db.relationship('ItemImage', backref='item', lazy=True, cascade="all, delete-orphan")

class ItemImage(db.Model):
    """Model to store item images"""
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # Original filename
    file_path = db.Column(db.String(500), nullable=False)  # Path where file is stored
    file_size = db.Column(db.Integer)  # File size in bytes
    mime_type = db.Column(db.String(100))  # MIME type (image/jpeg, image/png, etc.)
    is_primary = db.Column(db.Boolean, default=False)  # Mark primary image for display
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_url(self):
        """Generate URL for the image"""
        return f"/uploads/items/{self.file_path}"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role_settings = db.relationship('UserRoleSettings', backref='user', uselist=False, cascade='all, delete-orphan')

class UserRoleSettings(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    isSeller = db.Column(db.Boolean, default=False)
    address = db.Column(db.String(255))

class Cart(db.Model):
    id_item = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Orders(db.Model):
    id_order = db.Column(db.Integer, primary_key=True)
    id_item = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)