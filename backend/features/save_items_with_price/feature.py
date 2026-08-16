import uuid
from datetime import datetime
from decimal import Decimal
from flask import Blueprint, request, jsonify, g
from sqlalchemy import text
from functools import wraps
import re

bp = Blueprint('capability_save_items_with_price_bd77265a', __name__)

def get_db():
    """Get database connection from Flask g object"""
    from flask import current_app
    if 'db' not in g:
        g.db = current_app.config['DATABASE_ENGINE']
    return g.db

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'code': 'UNAUTHORIZED', 'message': 'Authentication required'}), 401
        
        # Extract user_id from Authorization header (assuming Bearer token format)
        # In production, this would validate the token and extract user_id
        try:
            token = auth_header.replace('Bearer ', '')
            # For this implementation, we assume the token contains or maps to a user_id
            # In a real system, you'd validate the token and extract the user_id
            user_id = getattr(g, 'user_id', None)
            if not user_id:
                # Attempt to get user_id from a hypothetical auth system
                # For now, we'll check if it's set in g by middleware
                if not hasattr(g, 'user_id'):
                    return jsonify({'code': 'UNAUTHORIZED', 'message': 'Authentication required'}), 401
        except Exception:
            return jsonify({'code': 'UNAUTHORIZED', 'message': 'Authentication required'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def is_valid_url(url):
    """Validate URL format"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

@bp.route('/api/capability_save_items_with_price_bd77265a/saved-items', methods=['POST'])
@require_auth
def create_saved_item():
    """Creates a new saved item with name, price, and product link for the authenticated user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'item_name' not in data or 'price' not in data or 'product_link' not in data:
            return jsonify({
                'code': 'VALIDATION_ERROR',
                'message': 'All three fields (item_name, price, product_link) are required'
            }), 400
        
        item_name = data.get('item_name')
        price = data.get('price')
        product_link = data.get('product_link')
        
        # Validate item_name
        if not item_name or not isinstance(item_name, str) or len(item_name) < 1 or len(item_name) > 500:
            return jsonify({
                'code': 'VALIDATION_ERROR',
                'message': 'All three fields (item_name, price, product_link) are required'
            }), 400
        
        # Validate price
        try:
            price_decimal = Decimal(str(price))
            if price_decimal < 0:
                return jsonify({
                    'code': 'INVALID_PRICE',
                    'message': 'Price must be a non-negative number'
                }), 400
            # Round to 2 decimal places
            price_decimal = price_decimal.quantize(Decimal('0.01'))
        except (ValueError, TypeError, Exception):
            return jsonify({
                'code': 'INVALID_PRICE',
                'message': 'Price must be a non-negative number'
            }), 400
        
        # Validate product_link
        if not product_link or not isinstance(product_link, str) or len(product_link) < 1 or len(product_link) > 2048:
            return jsonify({
                'code': 'VALIDATION_ERROR',
                'message': 'All three fields (item_name, price, product_link) are required'
            }), 400
        
        if not is_valid_url(product_link):
            return jsonify({
                'code': 'INVALID_URL',
                'message': 'Product link must be a valid URL'
            }), 400
        
        # Get user_id from g (set by auth middleware)
        user_id = g.user_id
        
        # Generate UUID and timestamp
        item_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        # Insert into database
        db = get_db()
        query = text("""
            INSERT INTO f_bd77265a__saved_items 
            (id, user_id, item_name, price, product_link, created_at)
            VALUES (:id, :user_id, :item_name, :price, :product_link, :created_at)
        """)
        
        with db.connect() as conn:
            conn.execute(query, {
                'id': item_id,
                'user_id': user_id,
                'item_name': item_name,
                'price': float(price_decimal),
                'product_link': product_link,
                'created_at': created_at
            })
            conn.commit()
        
        # Return created item
        return jsonify({
            'id': item_id,
            'user_id': user_id,
            'item_name': item_name,
            'price': float(price_decimal),
            'product_link': product_link,
            'created_at': created_at.isoformat() + 'Z'
        }), 201
        
    except Exception as e:
        return jsonify({
            'code': 'INTERNAL_ERROR',
            'message': 'Failed to save item'
        }), 500

@bp.route('/api/capability_save_items_with_price_bd77265a/saved-items', methods=['GET'])
@require_auth
def get_saved_items():
    """Retrieves the list of saved items for the authenticated user, ordered by creation time (newest first)"""
    try:
        user_id = g.user_id
        
        db = get_db()
        query = text("""
            SELECT id, user_id, item_name, price, product_link, created_at
            FROM f_bd77265a__saved_items
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """)
        
        with db.connect() as conn:
            result = conn.execute(query, {'user_id': user_id})
            rows = result.fetchall()
        
        items = []
        for row in rows:
            items.append({
                'id': row[0],
                'user_id': row[1],
                'item_name': row[2],
                'price': float(row[3]),
                'product_link': row[4],
                'created_at': row[5].isoformat() + 'Z' if hasattr(row[5], 'isoformat') else row[5]
            })
        
        return jsonify({'items': items}), 200
        
    except Exception as e:
        return jsonify({
            'code': 'INTERNAL_ERROR',
            'message': 'Failed to retrieve saved items'
        }), 500

@bp.route('/api/capability_save_items_with_price_bd77265a/saved-items/<id>', methods=['GET'])
@require_auth
def get_saved_item_by_id(id):
    """Retrieves a single saved item by its ID for the authenticated user"""
    try:
        user_id = g.user_id
        
        db = get_db()
        query = text("""
            SELECT id, user_id, item_name, price, product_link, created_at
            FROM f_bd77265a__saved_items
            WHERE id = :id AND user_id = :user_id
        """)
        
        with db.connect() as conn:
            result = conn.execute(query, {'id': id, 'user_id': user_id})
            row = result.fetchone()
        
        if not row:
            return jsonify({
                'code': 'NOT_FOUND',
                'message': 'Saved item not found or does not belong to user'
            }), 404
        
        item = {
            'id': row[0],
            'user_id': row[1],
            'item_name': row[2],
            'price': float(row[3]),
            'product_link': row[4],
            'created_at': row[5].isoformat() + 'Z' if hasattr(row[5], 'isoformat') else row[5]
        }
        
        return jsonify(item), 200
        
    except Exception as e:
        return jsonify({
            'code': 'INTERNAL_ERROR',
            'message': 'Failed to retrieve saved item'
        }), 500
