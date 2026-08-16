from flask import Blueprint, request, jsonify, g
from functools import wraps
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os

bp = Blueprint('capability_track_estimated_money_saved_66579af4', __name__)

def get_db_connection():
    """Get database connection from Flask app context or create new one."""
    if not hasattr(g, 'db_engine'):
        database_url = os.environ.get('DATABASE_URL', 'mysql+pymysql://user:password@localhost/dbname')
        g.db_engine = create_engine(database_url, pool_pre_ping=True)
    return g.db_engine.connect()

def require_auth(f):
    """Decorator to require authentication for endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'UNAUTHORIZED', 'message': 'Authentication required'}), 401
        
        # Extract user_id from token (simplified - in production use proper JWT validation)
        try:
            # Assuming Bearer token format: "Bearer <user_id>" or just user_id
            token = auth_header.replace('Bearer ', '').strip()
            g.user_id = token
        except Exception:
            return jsonify({'error': 'UNAUTHORIZED', 'message': 'Authentication required'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/api/capability_track_estimated_money_saved_66579af4/savings/record', methods=['POST'])
@require_auth
def record_savings():
    """Records a new savings entry when a user skips an item and updates the user's total savings amount."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'INVALID_REQUEST', 'message': 'Request body is required'}), 400
        
        # Validate required fields
        item_id = data.get('item_id')
        saved_amount = data.get('saved_amount')
        
        if not item_id:
            return jsonify({'error': 'INVALID_REQUEST', 'message': 'item_id is required'}), 400
        
        if saved_amount is None:
            return jsonify({'error': 'INVALID_REQUEST', 'message': 'saved_amount is required'}), 400
        
        # Validate saved_amount
        try:
            saved_amount = Decimal(str(saved_amount))
            if saved_amount < 0:
                return jsonify({'error': 'INVALID_AMOUNT', 'message': 'Saved amount must be a positive number'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'INVALID_AMOUNT', 'message': 'Saved amount must be a positive number'}), 400
        
        # Validate UUID format
        try:
            uuid.UUID(item_id)
        except ValueError:
            return jsonify({'error': 'INVALID_REQUEST', 'message': 'item_id must be a valid UUID'}), 400
        
        user_id = g.user_id
        savings_record_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        conn = get_db_connection()
        
        try:
            # Start transaction
            trans = conn.begin()
            
            # Check if user_savings_totals record exists, if not create it
            check_user_query = text("""
                SELECT user_id, total_saved FROM f_66579af4__user_savings_totals 
                WHERE user_id = :user_id FOR UPDATE
            """)
            user_result = conn.execute(check_user_query, {'user_id': user_id}).fetchone()
            
            if user_result is None:
                # Create new user_savings_totals record
                insert_user_query = text("""
                    INSERT INTO f_66579af4__user_savings_totals (user_id, total_saved, updated_at)
                    VALUES (:user_id, :saved_amount, :updated_at)
                """)
                conn.execute(insert_user_query, {
                    'user_id': user_id,
                    'saved_amount': saved_amount,
                    'updated_at': now
                })
                new_total_saved = saved_amount
            else:
                # Update existing user_savings_totals record
                current_total = Decimal(str(user_result[1]))
                new_total_saved = current_total + saved_amount
                
                update_user_query = text("""
                    UPDATE f_66579af4__user_savings_totals 
                    SET total_saved = :new_total, updated_at = :updated_at
                    WHERE user_id = :user_id
                """)
                conn.execute(update_user_query, {
                    'new_total': new_total_saved,
                    'updated_at': now,
                    'user_id': user_id
                })
            
            # Insert savings record
            insert_record_query = text("""
                INSERT INTO f_66579af4__savings_records 
                (id, user_id, item_id, saved_amount, skipped_at, created_at)
                VALUES (:id, :user_id, :item_id, :saved_amount, :skipped_at, :created_at)
            """)
            conn.execute(insert_record_query, {
                'id': savings_record_id,
                'user_id': user_id,
                'item_id': item_id,
                'saved_amount': saved_amount,
                'skipped_at': now,
                'created_at': now
            })
            
            trans.commit()
            
            return jsonify({
                'savings_record_id': savings_record_id,
                'new_total_saved': float(new_total_saved)
            }), 201
            
        except SQLAlchemyError as e:
            trans.rollback()
            # Check if it's a foreign key constraint error (item not found)
            if 'foreign key constraint' in str(e).lower() or 'cannot add or update a child row' in str(e).lower():
                return jsonify({'error': 'ITEM_NOT_FOUND', 'message': 'Referenced item does not exist'}), 404
            raise
        finally:
            conn.close()
            
    except SQLAlchemyError:
        return jsonify({'error': 'INTERNAL_ERROR', 'message': 'Failed to record savings'}), 500
    except Exception:
        return jsonify({'error': 'INTERNAL_ERROR', 'message': 'Failed to record savings'}), 500

@bp.route('/api/capability_track_estimated_money_saved_66579af4/savings/total', methods=['GET'])
@require_auth
def get_total_savings():
    """Retrieves the user's total estimated savings amount for prominent display in the app."""
    try:
        user_id = g.user_id
        
        conn = get_db_connection()
        
        try:
            query = text("""
                SELECT total_saved, updated_at 
                FROM f_66579af4__user_savings_totals 
                WHERE user_id = :user_id
            """)
            result = conn.execute(query, {'user_id': user_id}).fetchone()
            
            if result is None:
                return jsonify({'error': 'NO_SAVINGS_DATA', 'message': 'No savings data found for user'}), 404
            
            total_saved = float(result[0])
            updated_at = result[1].isoformat() if hasattr(result[1], 'isoformat') else str(result[1])
            
            return jsonify({
                'total_saved': total_saved,
                'updated_at': updated_at
            }), 200
            
        finally:
            conn.close()
            
    except SQLAlchemyError:
        return jsonify({'error': 'INTERNAL_ERROR', 'message': 'Failed to retrieve savings total'}), 500
    except Exception:
        return jsonify({'error': 'INTERNAL_ERROR', 'message': 'Failed to retrieve savings total'}), 500

@bp.route('/api/capability_track_estimated_money_saved_66579af4/savings/history', methods=['GET'])
@require_auth
def get_savings_history():
    """Retrieves the list of individual savings records to show the user how savings accumulated over time."""
    try:
        user_id = g.user_id
        
        # Get pagination parameters
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        # Validate parameters
        if limit < 1 or limit > 100:
            limit = 50
        if offset < 0:
            offset = 0
        
        conn = get_db_connection()
        
        try:
            # Get total count
            count_query = text("""
                SELECT COUNT(*) 
                FROM f_66579af4__savings_records 
                WHERE user_id = :user_id
            """)
            count_result = conn.execute(count_query, {'user_id': user_id}).fetchone()
            total_count = count_result[0]
            
            # Get paginated records
            records_query = text("""
                SELECT id, item_id, saved_amount, skipped_at, created_at 
                FROM f_66579af4__savings_records 
                WHERE user_id = :user_id
                ORDER BY skipped_at DESC, created_at DESC
                LIMIT :limit OFFSET :offset
            """)
            records_result = conn.execute(records_query, {
                'user_id': user_id,
                'limit': limit,
                'offset': offset
            }).fetchall()
            
            records = []
            for row in records_result:
                records.append({
                    'id': row[0],
                    'item_id': row[1],
                    'saved_amount': float(row[2]),
                    'skipped_at': row[3].isoformat() if hasattr(row[3], 'isoformat') else str(row[3]),
                    'created_at': row[4].isoformat() if hasattr(row[4], 'isoformat') else str(row[4])
                })
            
            return jsonify({
                'records': records,
                'total_count': total_count
            }), 200
            
        finally:
            conn.close()
            
    except SQLAlchemyError:
        return jsonify({'error': 'INTERNAL_ERROR', 'message': 'Failed to retrieve savings history'}), 500
    except Exception:
        return jsonify({'error': 'INTERNAL_ERROR', 'message': 'Failed to retrieve savings history'}), 500
