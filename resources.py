import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database import db
from models import Store, Item, User, UserRoleSettings, Cart, Orders, ItemImage
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
from datetime import timedelta

api_blueprint = Blueprint('api', __name__)

# Image upload configuration
UPLOAD_FOLDER = 'uploads/items'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_upload_folder():
    """Create upload directory if it doesn't exist"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

def compress_image(image_path, max_size=(800, 800), quality=85):
    """Compress and resize image to reduce file size"""
    try:
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if image is larger than max_size
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save with compression
            img.save(image_path, optimize=True, quality=quality)
        return True
    except Exception as e:
        print(f"Error compressing image: {e}")
        return False

# User Registration
@api_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 400

    hashed_password = generate_password_hash(data['password'])
    
    user = User(email=data['email'], password=hashed_password)
    user.role_settings = UserRoleSettings(isSeller=False, address='')
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

# User Login
@api_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    # ✅ Ensure identity is a string
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(hours=10)
        )

    print('console')
    return jsonify(access_token=access_token, user_id=user.id, email=user.email)

# Get All Users
@api_blueprint.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{'id': user.id, 'email': user.email} for user in users])

# Get a specific user setting
@api_blueprint.route('/UserRoleSettings/<int:user_id>', methods=['GET'])
def get_settings(user_id):
    roleSetting = UserRoleSettings.query.filter_by(id=user_id).first()
    return jsonify({'roleSettings': {'isSeller': roleSetting.isSeller, 'address': roleSetting.address}})

# set seller
@api_blueprint.route('/setseller', methods=['POST'])
def setSeller():
    data = request.get_json()
    userSettings = UserRoleSettings.query.get(data['id'])
    if not userSettings:
        return jsonify({'message': 'Usuario no encontrado'}), 404
    userSettings.isSeller = True
    db.session.commit()
    return jsonify({'roleSettings': {'isSeller': userSettings.isSeller}}), 201

# Get User data
@api_blueprint.route('/userData', methods=['GET'])
@jwt_required()  # Ensures only authenticated users can access
def get_user_data():
    user_id = get_jwt_identity()  # Extract user ID from the token
    user = User.query.get(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify({'id': user.id, 'email': user.email})

# Create Store
@api_blueprint.route('/store', methods=['POST'])
@jwt_required()
def create_store():
    print("empzadon")
    data = request.get_json()
    print('data store', data)
    if Store.query.filter_by(name=data['storename']).first():
        return jsonify({'message': 'Store already exists'}), 400

    store = Store(name=data['storename'])
    store.owner_id = data['userId']
    db.session.add(store)
    db.session.commit()
    return jsonify({'message': 'Store created'}), 201

# Get All Stores
@api_blueprint.route('/stores', methods=['GET'])
def get_stores():
    stores = Store.query.all()
    return jsonify([{'id': store.id, 'name': store.name} for store in stores])

# Get A Store by ownerId - mis stores en mi account
@api_blueprint.route('/stores/<int:user_id>', methods=['GET'])
def get_stores_by_owner(user_id):
    stores = Store.query.filter_by(owner_id=user_id).all()
    return jsonify([
        {'id': store.id, 'name': store.name, 'owner_id': store.owner_id}
        for store in stores
    ])

# Create Item
@api_blueprint.route('/store/<int:store_id>/item', methods=['POST'])
# @jwt_required()
def create_item(store_id):
    data = request.get_json()
    store = Store.query.get_or_404(store_id)

    item = Item(name=data['name'], price=data['price'], description= data['description'], store=store)
    print(item)
    db.session.add(item)
    db.session.commit()
    return jsonify({'message': 'Item created', 'item_id': item.id}), 201

# Get All Items in a Store (Updated with images)
@api_blueprint.route('/store/<int:store_id>/items', methods=['GET'])
def get_items(store_id):
    store = Store.query.get_or_404(store_id)
    items_data = []
    for item in store.items:
        primary_image = next((img for img in item.images if img.is_primary), None)
        items_data.append({
            'id': item.id,
            'name': item.name,
            'price': item.price,
            'description': item.description,
            'primary_image': primary_image.get_url() if primary_image else None
        })
    return jsonify(items_data)

# get a specific Store
@api_blueprint.route('/store/<int:store_id>', methods=['GET'])
@jwt_required()
def get_store(store_id):
    store = Store.query.filter_by(id=store_id).first()
    if not store:
        return jsonify({'message': 'Store not found'}), 404
    
    return jsonify({'store': {'id': store.id, 'name': store.name}})

# get a specific Item (Updated with images)
@api_blueprint.route('/item/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.query.filter_by(id=item_id).first()
    if not item:
        return jsonify({'message': 'Item not found'}), 404
    
    # Get images
    images = [{
        'id': img.id,
        'url': img.get_url(),
        'is_primary': img.is_primary,
        'filename': img.filename
    } for img in item.images]
    
    return jsonify({
        'item': {
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': item.price,
            'store_id': item.store_id,
            'images': images
        }
    })

# Delete Store
@api_blueprint.route('/store/<int:store_id>', methods=['DELETE'])
@jwt_required()
def delete_store(store_id):
    store = Store.query.get_or_404(store_id)
    db.session.delete(store)
    db.session.commit()
    return jsonify({'message': 'Store deleted'})

# Delete Item (Updated to handle images)
@api_blueprint.route('/item/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)

    # Delete associated images from filesystem
    for image in item.images:
        file_path = os.path.join(UPLOAD_FOLDER, image.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    # Verificar si el item está en el carrito
    cart_entries = Cart.query.filter_by(id_item=item_id).all()
    for cart_item in cart_entries:
        db.session.delete(cart_item)

    db.session.delete(item)
    db.session.commit()

    return jsonify({'message': 'Item deleted (and removed from cart if it was present)'})

# Edit Item
@api_blueprint.route('/item/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    data = request.get_json()

    item.name = data.get('name', item.name)
    item.price = data.get('price', item.price)
    item.description = data.get('description', item.description)

    db.session.commit()

    return jsonify({
        'message': 'Item updated',
        'item': {
            'id': item.id,
            'name': item.name,
            'price': item.price,
            'description': item.description
        }
    }), 200

# Edit Store
@api_blueprint.route('/store/<int:store_id>', methods=['PUT'])
@jwt_required()
def update_store(store_id):
    store = Store.query.get_or_404(store_id)
    data = request.get_json()

    store.name = data.get('name', store.name)

    db.session.commit()

    return jsonify({
        'message': 'Store updated',
        'store': {
            'id': store.id,
            'name': store.name
        }
    }), 200

# Get all items (paginated / lazy loading) - Updated with images
@api_blueprint.route('/items_paginated', methods=['GET'])
def get_all_items_paginated():
    # Parámetros de query para paginación
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)

    # Query paginada de todos los ítems
    paginated_items = Item.query.paginate(page=page, per_page=per_page, error_out=False)

    items_list = []
    for item in paginated_items.items:
        primary_image = next((img for img in item.images if img.is_primary), None)
        items_list.append({
            'id': item.id,
            'name': item.name,
            'price': item.price,
            'description': item.description,
            'store_id': item.store_id,
            'primary_image': primary_image.get_url() if primary_image else None
        })

    return jsonify({
        'items': items_list,
        'total': paginated_items.total,
        'page': paginated_items.page,
        'per_page': paginated_items.per_page,
        'pages': paginated_items.pages
    })

# IMAGE UPLOAD ENDPOINTS

@api_blueprint.route('/item/<int:item_id>/upload-image', methods=['POST'])
# @jwt_required()
def upload_item_image(item_id):
    """Upload single image for an item"""
    print('upload-image')
    create_upload_folder()
    
    # Check if item exists
    item = Item.query.get_or_404(item_id)
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
    
    try:
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            os.remove(file_path)
            return jsonify({'error': 'File too large. Maximum size: 5MB'}), 400
        
        # Compress image
        compress_image(file_path)
        
        # Update file size after compression
        file_size = os.path.getsize(file_path)
        
        # Check if this is the first image (make it primary)
        is_primary = len(item.images) == 0
        
        # Save to database
        item_image = ItemImage(
            item_id=item_id,
            filename=original_filename,
            file_path=unique_filename,
            file_size=file_size,
            mime_type=file.mimetype,
            is_primary=is_primary
        )
        
        db.session.add(item_image)
        db.session.commit()
        
        return jsonify({
            'message': 'Image uploaded successfully',
            'image': {
                'id': item_image.id,
                'filename': item_image.filename,
                'url': item_image.get_url(),
                'is_primary': item_image.is_primary,
                'file_size': item_image.file_size
            }
        }), 201
        
    except Exception as e:
        # Clean up file if database save fails
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@api_blueprint.route('/item/<int:item_id>/upload-multiple-images', methods=['POST'])
@jwt_required()
def upload_multiple_item_images(item_id):
    """Upload multiple images for an item"""
    create_upload_folder()
    
    # Check if item exists
    item = Item.query.get_or_404(item_id)
    
    if 'images' not in request.files:
        return jsonify({'error': 'No image files provided'}), 400
    
    files = request.files.getlist('images')
    
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No files selected'}), 400
    
    uploaded_images = []
    errors = []
    
    for i, file in enumerate(files):
        if file.filename == '':
            continue
            
        if not allowed_file(file.filename):
            errors.append(f"File {i+1}: Invalid file type")
            continue
        
        try:
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            
            # Save file
            file.save(file_path)
            
            # Get file info
            file_size = os.path.getsize(file_path)
            
            # Check file size
            if file_size > MAX_FILE_SIZE:
                os.remove(file_path)
                errors.append(f"File {i+1}: Too large (max 5MB)")
                continue
            
            # Compress image
            compress_image(file_path)
            
            # Update file size after compression
            file_size = os.path.getsize(file_path)
            
            # Check if this is the first image (make it primary)
            is_primary = len(item.images) == 0 and len(uploaded_images) == 0
            
            # Save to database
            item_image = ItemImage(
                item_id=item_id,
                filename=original_filename,
                file_path=unique_filename,
                file_size=file_size,
                mime_type=file.mimetype,
                is_primary=is_primary
            )
            
            db.session.add(item_image)
            uploaded_images.append({
                'id': item_image.id,
                'filename': original_filename,
                'url': item_image.get_url(),
                'is_primary': is_primary
            })
            
        except Exception as e:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            errors.append(f"File {i+1}: Upload failed - {str(e)}")
    
    if uploaded_images:
        db.session.commit()
    
    return jsonify({
        'message': f'{len(uploaded_images)} images uploaded successfully',
        'images': uploaded_images,
        'errors': errors
    }), 201 if uploaded_images else 400

@api_blueprint.route('/item/<int:item_id>/images', methods=['GET'])
def get_item_images(item_id):
    """Get all images for an item"""
    item = Item.query.get_or_404(item_id)
    
    images = [{
        'id': img.id,
        'filename': img.filename,
        'url': img.get_url(),
        'is_primary': img.is_primary,
        'file_size': img.file_size,
        'uploaded_at': img.uploaded_at.isoformat()
    } for img in item.images]
    
    return jsonify({'images': images})

@api_blueprint.route('/image/<int:image_id>/set-primary', methods=['PUT'])
@jwt_required()
def set_primary_image(image_id):
    """Set an image as primary for its item"""
    image = ItemImage.query.get_or_404(image_id)
    
    # Remove primary flag from other images of the same item
    ItemImage.query.filter_by(item_id=image.item_id).update({'is_primary': False})
    
    # Set this image as primary
    image.is_primary = True
    db.session.commit()
    
    return jsonify({'message': 'Primary image updated'})

@api_blueprint.route('/image/<int:image_id>', methods=['DELETE'])
@jwt_required()
def delete_image(image_id):
    """Delete an image"""
    image = ItemImage.query.get_or_404(image_id)
    
    # Delete file from filesystem
    file_path = os.path.join(UPLOAD_FOLDER, image.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # If deleting primary image, set another image as primary
    if image.is_primary:
        other_images = ItemImage.query.filter(
            ItemImage.item_id == image.item_id,
            ItemImage.id != image.id
        ).first()
        if other_images:
            other_images.is_primary = True
    
    # Delete from database
    db.session.delete(image)
    db.session.commit()
    
    return jsonify({'message': 'Image deleted successfully'})

# Serve uploaded files
@api_blueprint.route('/uploads/items/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded images"""
    return send_from_directory(UPLOAD_FOLDER, filename)

# Add to Cart
@api_blueprint.route('/addtocart', methods=['POST'])
@jwt_required()
def add_to_cart():
    print("addtocart")
    data = request.get_json()
    print('data cart', data)

    itemInCart = Cart(id_item=data['itemId'])
    itemInCart.user_id = data['userId']
    db.session.add(itemInCart)
    db.session.commit()
    return jsonify({'message': 'imtem in cart created'}), 201

# Get All Items in your cart
@api_blueprint.route('/cart/<int:user_id>/item_ids', methods=['GET'])
def get_item_ids_in_cart(user_id):
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    item_ids = [item.id_item for item in cart_items]
    return jsonify({'id_item': item_ids})

@api_blueprint.route('/items_by_ids', methods=['POST'])
@jwt_required()
def get_items_by_ids():
    data = request.get_json()
    item_ids = data.get('item_ids', [])

    if not isinstance(item_ids, list) or not all(isinstance(i, int) for i in item_ids):
        return jsonify({'error': 'Invalid item_ids list'}), 400

    items = Item.query.filter(Item.id.in_(item_ids)).all()

    items_data = []
    for item in items:
        primary_image = next((img for img in item.images if img.is_primary), None)
        items_data.append({
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': item.price,
            'store_id': item.store_id,
            'primary_image': primary_image.get_url() if primary_image else None
        })

    return jsonify(items_data)

# Delete Item from cart
@api_blueprint.route('/item/cart/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item_from_cart(item_id):
    item = Cart.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted'})

#create order
@api_blueprint.route('/placeorder', methods=['POST'])
@jwt_required()
def create_order():
    user_id = get_jwt_identity()  # Obtenemos el ID del usuario desde el token JWT
    data = request.get_json()
    item_ids = data.get('item_ids', [])

    if not isinstance(item_ids, list) or not all(isinstance(i, int) for i in item_ids):
        return jsonify({'error': 'Invalid item_ids list'}), 400

    # Obtener ítems válidos del carrito del usuario
    cart_items = Cart.query.filter(Cart.user_id == user_id, Cart.id_item.in_(item_ids)).all()
    if not cart_items:
        return jsonify({'message': 'No items in cart matched'}), 400

    # Crear las órdenes y eliminar del carrito
    for cart_item in cart_items:
        new_order = Orders(id_item=cart_item.id_item, user_id=user_id)
        db.session.add(new_order)
        db.session.delete(cart_item)

    db.session.commit()

    return jsonify({'message': 'Order placed and items removed from cart'}), 201

@api_blueprint.route('/myorders/<int:user_id>/item_ids', methods=['GET'])
def get_item_ids_in_orders(user_id):
    order_items = Orders.query.filter_by(user_id=user_id).all()
    item_ids = [item.id_item for item in order_items]
    return jsonify({'id_item': item_ids})