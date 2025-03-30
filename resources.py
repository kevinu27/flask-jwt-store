from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database import db
from models import Store, Item, User
from werkzeug.security import generate_password_hash, check_password_hash

api_blueprint = Blueprint('api', __name__)

# User Registration
@api_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'User already exists'}), 400

    hashed_password = generate_password_hash(data['password'])
    user = User(username=data['username'], password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

# User Login
@api_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    # ✅ Ensure identity is a string
    access_token = create_access_token(identity=str(user.id))

    print('console')
    return jsonify(access_token=access_token, user_id=user.id, username=user.username)
    # return jsonify(access_token=access_token)

# Get All Users
@api_blueprint.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{'id': user.id, 'username': user.username} for user in users])


# Get User data
@api_blueprint.route('/userData', methods=['GET'])
@jwt_required()  # Ensures only authenticated users can access
def get_user_data():
    user_id = get_jwt_identity()  # Extract user ID from the token
    user = User.query.get(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify({'id': user.id, 'username': user.username})


# Create Store
@api_blueprint.route('/store', methods=['POST'])
@jwt_required()
def create_store():
    print("empzadon")
    data = request.get_json()
    print('data', data)
    if Store.query.filter_by(name=data['name']).first():
        return jsonify({'message': 'Store already exists'}), 400

    store = Store(name=data['name'])
    db.session.add(store)
    db.session.commit()
    return jsonify({'message': 'Store created'}), 201

# Get All Stores
@api_blueprint.route('/stores', methods=['GET'])
def get_stores():
    stores = Store.query.all()
    return jsonify([{'id': store.id, 'name': store.name} for store in stores])

# Create Item
@api_blueprint.route('/store/<int:store_id>/item', methods=['POST'])
@jwt_required()
def create_item(store_id):
    data = request.get_json()
    store = Store.query.get_or_404(store_id)

    item = Item(name=data['name'], price=data['price'], store=store)
    db.session.add(item)
    db.session.commit()
    return jsonify({'message': 'Item created'}), 201

# Get All Items in a Store
@api_blueprint.route('/store/<int:store_id>/items', methods=['GET'])
def get_items(store_id):
    store = Store.query.get_or_404(store_id)
    return jsonify([{'id': item.id, 'name': item.name, 'price': item.price} for item in store.items])

# get a specific Store
@api_blueprint.route('/store/<int:store_id>', methods=['GET'])
@jwt_required()
def get_store(store_id):
    store = Store.query.filter_by(id=store_id).first()
    if not store:
        return jsonify({'message': 'Store not found'}), 404
    
    return jsonify({'store': {'id': store.id, 'name': store.name}})

# Delete Store
@api_blueprint.route('/store/<int:store_id>', methods=['DELETE'])
@jwt_required()
def delete_store(store_id):
    store = Store.query.get_or_404(store_id)
    db.session.delete(store)
    db.session.commit()
    return jsonify({'message': 'Store deleted'})

# Delete Item
@api_blueprint.route('/item/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted'})
