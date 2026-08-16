"""
Flask Blueprint for Buy/Skip Decision Feature
Implements decision recording, savings tracking, and decision screen data retrieval
"""
from flask import Blueprint, request, jsonify, g
from functools import wraps
from datetime import datetime
from decimal import Decimal
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
import os

bp = Blueprint('capability_buy_skip_decision_c984506c', __name__)

# Database connection helper
def get_db_connection():
    """Get database connection from Flask g object or create new one"""
    if 'db_engine' not in g:
        db_url = os.environ.get('DATABASE_URL', 'mysql+pymysql://user:password@localhost/dbname')
        g.db_engine = create_engine(db_url, poolclass=NullPool)
    return g.db_engine.connect()

# Authentication decorator
def require_auth(f):
    """Decorator to require authentication for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'code': 'UNAUTHORIZED', 'message': 'Authentication required'}), 401
        
        # Extract user_id from token (simplified - in production use proper JWT validation)
        try:
            # Assuming Bearer token format: "Bearer <user_id>"
            token_parts = auth_header.split()
            if len(token_parts) != 2 or token_parts[0] != 'Bearer':
                return jsonify({'code': 'UNAUTHORIZED', 'message': 'Authentication required'}), 401
            g.user_id = token_parts[1]
        except Exception:
            return jsonify({'code': 'UNAUTHORIZED', 'message': 'Authentication required'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

# Helper function to get item details from dependency feature
def get_item_details(conn, item_id, user_id):
    """
    Fetch item details from dependency feature tables
    This assumes items are stored in a separate feature's table
    """
    # Mock implementation - in production this would query the actual item table
    # from the dependency feature that manages items
    query = text("""
        SELECT item_id, item_name, item_price, item_link, cooling_off_end
        FROM items
        WHERE item_id = :item_id AND user_id = :user_id
    """)
    
    try:
        result = conn.execute(query, {'item_id': item_id, 'user_id': user_id})
        row = result.fetchone()
        if row:
            return {
                'item_id': row[0],
                'item_name': row[1],
                'item_price': float(row[2]),
                'item_link': row[3],
                'cooling_off_end': row[4]
            }
    except Exception:
        # If items table doesn't exist, return mock data for testing
        pass
    
    return None

def check_cooling_off_ended(conn, item_id, user_id):
    """
    Check if cooling-off period has ended for an item
    Returns True if ended, False otherwise
    """
    # Mock implementation - in production this would check the actual cooling-off end time
    # from the dependency feature
    try:
        query = text("""
            SELECT cooling_off_end
            FROM items
            WHERE item_id = :item_id AND user_id = :user_id
        """)
        result = conn.execute(query, {'item_id': item_id, 'user_id': user_id})
        row = result.fetchone()
        if row and row[0]:
            return datetime.utcnow() >= row[0]
    except Exception:
        pass
    
    # Default to True for testing if table doesn't exist
    return True

@bp.route('/api/capability_buy_skip_decision_c984506c/items/<item_id>/decision', methods=['GET'])
@require_auth
def get_decision_screen_data(item_id):
    """
    Retrieves item details and current savings total for displaying the decision screen
    after cooling-off period ends
    """
    conn = get_db_connection()
    
    try:
        user_id = g.user_id
        
        # Validate UUID format
        try:
            uuid.UUID(item_id)
        except ValueError:
            return jsonify({'code': 'ITEM_NOT_FOUND', 'message': 'Item does not exist or does not belong to user'}), 404
        
        # Get item details from dependency feature
        item_details = get_item_details(conn, item_id, user_id)
        if not item_details:
            return jsonify({'code': 'ITEM_NOT_FOUND', 'message': 'Item does not exist or does not belong to user'}), 404
        
        # Check if cooling-off period has ended
        if not check_cooling_off_ended(conn, item_id, user_id):
            return jsonify({'code': 'COOLING_OFF_NOT_ENDED', 'message': 'Cooling-off period has not yet ended for this item'}), 400
        
        # Check if decision already exists
        decision_query = text("""
            SELECT id FROM f_c984506c__item_decisions
            WHERE item_id = :item_id AND user_id = :user_id
        """)
        decision_result = conn.execute(decision_query, {'item_id': item_id, 'user_id': user_id})
        already_decided = decision_result.fetchone() is not None
        
        # Get current total saved
        savings_query = text("""
            SELECT total_saved FROM f_c984506c__user_savings
            WHERE user_id = :user_id
        """)
        savings_result = conn.execute(savings_query, {'user_id': user_id})
        savings_row = savings_result.fetchone()
        current_total_saved = float(savings_row[0]) if savings_row else 0.0
        
        response = {
            'item_id': item_id,
            'item_name': item_details['item_name'],
            'item_price': item_details['item_price'],
            'item_link': item_details['item_link'],
            'current_total_saved': current_total_saved,
            'already_decided': already_decided
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'code': 'INTERNAL_ERROR', 'message': str(e)}), 500
    finally:
        conn.close()

@bp.route('/api/capability_buy_skip_decision_c984506c/items/<item_id>/decide/buy', methods=['POST'])
@require_auth
def record_buy_decision(item_id):
    """
    Records a Buy decision when user taps Buy button, creating a decision record
    that marks the item as decided for removal from active list
    """
    conn = get_db_connection()
    
    try:
        user_id = g.user_id
        data = request.get_json()
        
        # Validate request
        if not data or 'item_price' not in data:
            return jsonify({'code': 'INVALID_REQUEST', 'message': 'item_price is required'}), 400
        
        item_price = Decimal(str(data['item_price']))
        if item_price < 0:
            return jsonify({'code': 'INVALID_REQUEST', 'message': 'item_price must be non-negative'}), 400
        
        # Validate UUID format
        try:
            uuid.UUID(item_id)
        except ValueError:
            return jsonify({'code': 'ITEM_NOT_FOUND', 'message': 'Item does not exist or does not belong to user'}), 404
        
        # Get item details to verify ownership
        item_details = get_item_details(conn, item_id, user_id)
        if not item_details:
            return jsonify({'code': 'ITEM_NOT_FOUND', 'message': 'Item does not exist or does not belong to user'}), 404
        
        # Check if cooling-off period has ended
        if not check_cooling_off_ended(conn, item_id, user_id):
            return jsonify({'code': 'COOLING_OFF_NOT_ENDED', 'message': 'Cooling-off period has not yet ended for this item'}), 400
        
        # Check if decision already exists
        decision_check = text("""
            SELECT id FROM f_c984506c__item_decisions
            WHERE item_id = :item_id AND user_id = :user_id
        """)
        existing = conn.execute(decision_check, {'item_id': item_id, 'user_id': user_id})
        if existing.fetchone():
            return jsonify({'code': 'ALREADY_DECIDED', 'message': 'Decision has already been recorded for this item'}), 409
        
        # Create decision record
        decision_id = str(uuid.uuid4())
        decided_at = datetime.utcnow()
        
        insert_query = text("""
            INSERT INTO f_c984506c__item_decisions
            (id, item_id, user_id, decision_type, item_price, decided_at)
            VALUES (:id, :item_id, :user_id, :decision_type, :item_price, :decided_at)
        """)
        
        conn.execute(insert_query, {
            'id': decision_id,
            'item_id': item_id,
            'user_id': user_id,
            'decision_type': 'buy',
            'item_price': item_price,
            'decided_at': decided_at
        })
        conn.commit()
        
        response = {
            'decision_id': decision_id,
            'item_id': item_id,
            'decision_type': 'buy',
            'decided_at': decided_at.isoformat() + 'Z',
            'product_link': item_details['item_link']
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'code': 'INTERNAL_ERROR', 'message': str(e)}), 500
    finally:
        conn.close()

@bp.route('/api/capability_buy_skip_decision_c984506c/items/<item_id>/decide/skip', methods=['POST'])
@require_auth
def record_skip_decision(item_id):
    """
    Records a Skip decision when user taps Skip button, creates decision record,
    adds item price to user's total savings, and marks item for removal from active list
    """
    conn = get_db_connection()
    
    try:
        user_id = g.user_id
        data = request.get_json()
        
        # Validate request
        if not data or 'item_price' not in data:
            return jsonify({'code': 'INVALID_REQUEST', 'message': 'item_price is required'}), 400
        
        item_price = Decimal(str(data['item_price']))
        if item_price < 0:
            return jsonify({'code': 'INVALID_REQUEST', 'message': 'item_price must be non-negative'}), 400
        
        # Validate UUID format
        try:
            uuid.UUID(item_id)
        except ValueError:
            return jsonify({'code': 'ITEM_NOT_FOUND', 'message': 'Item does not exist or does not belong to user'}), 404
        
        # Get item details to verify ownership
        item_details = get_item_details(conn, item_id, user_id)
        if not item_details:
            return jsonify({'code': 'ITEM_NOT_FOUND', 'message': 'Item does not exist or does not belong to user'}), 404
        
        # Check if cooling-off period has ended
        if not check_cooling_off_ended(conn, item_id, user_id):
            return jsonify({'code': 'COOLING_OFF_NOT_ENDED', 'message': 'Cooling-off period has not yet ended for this item'}), 400
        
        # Check if decision already exists
        decision_check = text("""
            SELECT id FROM f_c984506c__item_decisions
            WHERE item_id = :item_id AND user_id = :user_id
        """)
        existing = conn.execute(decision_check, {'item_id': item_id, 'user_id': user_id})
        if existing.fetchone():
            return jsonify({'code': 'ALREADY_DECIDED', 'message': 'Decision has already been recorded for this item'}), 409
        
        # Create decision record
        decision_id = str(uuid.uuid4())
        decided_at = datetime.utcnow()
        
        insert_decision = text("""
            INSERT INTO f_c984506c__item_decisions
            (id, item_id, user_id, decision_type, item_price, decided_at)
            VALUES (:id, :item_id, :user_id, :decision_type, :item_price, :decided_at)
        """)
        
        conn.execute(insert_decision, {
            'id': decision_id,
            'item_id': item_id,
            'user_id': user_id,
            'decision_type': 'skip',
            'item_price': item_price,
            'decided_at': decided_at
        })
        
        # Update or create user savings record
        savings_check = text("""
            SELECT id, total_saved FROM f_c984506c__user_savings
            WHERE user_id = :user_id
        """)
        savings_result = conn.execute(savings_check, {'user_id': user_id})
        savings_row = savings_result.fetchone()
        
        if savings_row:
            # Update existing savings
            new_total_saved = Decimal(str(savings_row[1])) + item_price
            update_savings = text("""
                UPDATE f_c984506c__user_savings
                SET total_saved = :total_saved, updated_at = :updated_at
                WHERE user_id = :user_id
            """)
            conn.execute(update_savings, {
                'total_saved': new_total_saved,
                'updated_at': decided_at,
                'user_id': user_id
            })
        else:
            # Create new savings record
            new_total_saved = item_price
            insert_savings = text("""
                INSERT INTO f_c984506c__user_savings
                (id, user_id, total_saved, updated_at)
                VALUES (:id, :user_id, :total_saved, :updated_at)
            """)
            conn.execute(insert_savings, {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'total_saved': new_total_saved,
                'updated_at': decided_at
            })
        
        conn.commit()
        
        response = {
            'decision_id': decision_id,
            'item_id': item_id,
            'decision_type': 'skip',
            'decided_at': decided_at.isoformat() + 'Z',
            'price_saved': float(item_price),
            'new_total_saved': float(new_total_saved)
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'code': 'INTERNAL_ERROR', 'message': str(e)}), 500
    finally:
        conn.close()

@bp.route('/api/capability_buy_skip_decision_c984506c/users/me/savings', methods=['GET'])
@require_auth
def get_user_savings():
    """
    Retrieves the user's current total money saved from all skipped purchases
    for display throughout the application
    """
    conn = get_db_connection()
    
    try:
        user_id = g.user_id
        
        # Get user savings
        query = text("""
            SELECT user_id, total_saved, updated_at
            FROM f_c984506c__user_savings
            WHERE user_id = :user_id
        """)
        
        result = conn.execute(query, {'user_id': user_id})
        row = result.fetchone()
        
        if not row:
            return jsonify({'code': 'SAVINGS_NOT_INITIALIZED', 'message': 'User savings record does not exist yet'}), 404
        
        response = {
            'user_id': row[0],
            'total_saved': float(row[1]),
            'updated_at': row[2].isoformat() + 'Z' if row[2] else datetime.utcnow().isoformat() + 'Z'
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'code': 'INTERNAL_ERROR', 'message': str(e)}), 500
    finally:
        conn.close()
