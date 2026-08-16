import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from functools import wraps

from backend.core.db import get_engine

bp = Blueprint('capability_set_cooling_off_period_ed5144db', __name__)

def get_db_connection():
    """Open a connection using the shared environment configuration."""
    return get_engine().connect()

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for authentication token/session
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'error': 'UNAUTHORIZED',
                'message': 'Authentication required'
            }), 401
        
        # Store user info in g for use in route handlers
        g.user_id = auth_header  # Simplified - in production, validate token
        return f(*args, **kwargs)
    return decorated_function

def require_internal_auth(f):
    """Decorator to require internal/background job authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'error': 'UNAUTHORIZED',
                'message': 'Authentication required'
            }), 401
        
        # Check if this is an internal/background job token
        internal_token = request.headers.get('X-Internal-Token')
        if not internal_token:
            return jsonify({
                'error': 'FORBIDDEN',
                'message': 'Internal endpoint accessible only to background jobs'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/api/capability_set_cooling_off_period_ed5144db/cooling-periods', methods=['POST'])
@require_auth
def create_cooling_period():
    """Creates a new cooling period record when a user selects 1, 3, or 7 days during item save."""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'error': 'MISSING_REQUIRED_FIELD',
            'message': 'saved_item_id and period_days are required'
        }), 400
    
    saved_item_id = data.get('saved_item_id')
    period_days = data.get('period_days')
    
    # Validate required fields
    if not saved_item_id or period_days is None:
        return jsonify({
            'error': 'MISSING_REQUIRED_FIELD',
            'message': 'saved_item_id and period_days are required'
        }), 400
    
    # Validate period_days
    if period_days not in [1, 3, 7]:
        return jsonify({
            'error': 'INVALID_PERIOD_DAYS',
            'message': 'period_days must be 1, 3, or 7'
        }), 400
    
    # Validate UUID format
    try:
        uuid.UUID(saved_item_id)
    except (ValueError, AttributeError):
        return jsonify({
            'error': 'MISSING_REQUIRED_FIELD',
            'message': 'saved_item_id and period_days are required'
        }), 400
    
    conn = get_db_connection()
    
    try:
        # Check if saved_item exists (assuming there's a saved_items table)
        # For this implementation, we'll check if a cooling period already exists
        check_query = text("""
            SELECT id FROM f_ed5144db__cooling_periods 
            WHERE saved_item_id = :saved_item_id
        """)
        existing = conn.execute(check_query, {'saved_item_id': saved_item_id}).fetchone()
        
        if existing:
            return jsonify({
                'error': 'COOLING_PERIOD_ALREADY_EXISTS',
                'message': 'A cooling period already exists for this saved item'
            }), 409
        
        # Create new cooling period
        cooling_period_id = str(uuid.uuid4())
        now = datetime.utcnow()
        started_at = now
        expires_at = now + timedelta(days=period_days)
        created_at = now
        
        insert_query = text("""
            INSERT INTO f_ed5144db__cooling_periods 
            (id, saved_item_id, period_days, started_at, expires_at, created_at)
            VALUES (:id, :saved_item_id, :period_days, :started_at, :expires_at, :created_at)
        """)
        
        conn.execute(insert_query, {
            'id': cooling_period_id,
            'saved_item_id': saved_item_id,
            'period_days': period_days,
            'started_at': started_at,
            'expires_at': expires_at,
            'created_at': created_at
        })
        conn.commit()
        
        return jsonify({
            'id': cooling_period_id,
            'saved_item_id': saved_item_id,
            'period_days': period_days,
            'started_at': started_at.isoformat() + 'Z',
            'expires_at': expires_at.isoformat() + 'Z',
            'created_at': created_at.isoformat() + 'Z'
        }), 201
        
    except IntegrityError as e:
        conn.rollback()
        # Check if it's a duplicate key error
        if 'Duplicate entry' in str(e):
            return jsonify({
                'error': 'COOLING_PERIOD_ALREADY_EXISTS',
                'message': 'A cooling period already exists for this saved item'
            }), 409
        # Check constraint violation
        return jsonify({
            'error': 'INVALID_PERIOD_DAYS',
            'message': 'period_days must be 1, 3, or 7'
        }), 400
    except Exception as e:
        conn.rollback()
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500
    finally:
        conn.close()

@bp.route('/api/capability_set_cooling_off_period_ed5144db/cooling-periods/<saved_item_id>', methods=['GET'])
@require_auth
def get_cooling_period(saved_item_id):
    """Retrieves the cooling period record for a saved item to enable countdown display."""
    # Validate UUID format
    try:
        uuid.UUID(saved_item_id)
    except (ValueError, AttributeError):
        return jsonify({
            'error': 'COOLING_PERIOD_NOT_FOUND',
            'message': 'No cooling period found for the specified saved_item_id'
        }), 404
    
    conn = get_db_connection()
    
    try:
        query = text("""
            SELECT id, saved_item_id, period_days, started_at, expires_at, created_at
            FROM f_ed5144db__cooling_periods
            WHERE saved_item_id = :saved_item_id
        """)
        
        result = conn.execute(query, {'saved_item_id': saved_item_id}).fetchone()
        
        if not result:
            return jsonify({
                'error': 'COOLING_PERIOD_NOT_FOUND',
                'message': 'No cooling period found for the specified saved_item_id'
            }), 404
        
        now = datetime.utcnow()
        expires_at = result[4]
        
        # Calculate time remaining
        if now >= expires_at:
            time_remaining_seconds = 0
            is_expired = True
        else:
            time_remaining_seconds = int((expires_at - now).total_seconds())
            is_expired = False
        
        response = {
            'id': result[0],
            'saved_item_id': result[1],
            'period_days': result[2],
            'started_at': result[3].isoformat() + 'Z',
            'expires_at': result[4].isoformat() + 'Z',
            'created_at': result[5].isoformat() + 'Z',
            'time_remaining_seconds': time_remaining_seconds,
            'is_expired': is_expired
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500
    finally:
        conn.close()

@bp.route('/api/internal/cooling-periods/expired', methods=['GET'])
@require_internal_auth
def list_expired_cooling_periods():
    """Background job function that queries cooling periods where expires_at is in the past."""
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    # Validate parameters
    if limit < 1 or limit > 1000:
        limit = 100
    if offset < 0:
        offset = 0
    
    conn = get_db_connection()
    
    try:
        now = datetime.utcnow()
        
        # Get total count
        count_query = text("""
            SELECT COUNT(*) as total
            FROM f_ed5144db__cooling_periods
            WHERE expires_at <= :now
        """)
        total_count = conn.execute(count_query, {'now': now}).fetchone()[0]
        
        # Get paginated results
        query = text("""
            SELECT id, saved_item_id, period_days, started_at, expires_at, created_at
            FROM f_ed5144db__cooling_periods
            WHERE expires_at <= :now
            ORDER BY expires_at ASC
            LIMIT :limit OFFSET :offset
        """)
        
        results = conn.execute(query, {
            'now': now,
            'limit': limit,
            'offset': offset
        }).fetchall()
        
        cooling_periods = []
        for row in results:
            cooling_periods.append({
                'id': row[0],
                'saved_item_id': row[1],
                'period_days': row[2],
                'started_at': row[3].isoformat() + 'Z',
                'expires_at': row[4].isoformat() + 'Z',
                'created_at': row[5].isoformat() + 'Z'
            })
        
        return jsonify({
            'cooling_periods': cooling_periods,
            'total_count': total_count
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500
    finally:
        conn.close()

@bp.teardown_app_request
def teardown_db(exception=None):
    """Close database connection at end of request."""
    db_engine = g.pop('db_engine', None)
    if db_engine is not None:
        db_engine.dispose()


def process_expired_cooling_periods():
    """Return expired cooling periods for an in-process background worker."""
    now = datetime.utcnow()
    with get_db_connection() as conn:
        rows = conn.execute(text("""
            SELECT id, saved_item_id, period_days, started_at, expires_at, created_at
            FROM f_ed5144db__cooling_periods
            WHERE expires_at <= :now
            ORDER BY expires_at ASC
            LIMIT 100
        """), {'now': now}).fetchall()
    return {
        'cooling_periods': [
            {
                'id': row[0],
                'saved_item_id': row[1],
                'period_days': row[2],
                'started_at': row[3].isoformat() + 'Z',
                'expires_at': row[4].isoformat() + 'Z',
                'created_at': row[5].isoformat() + 'Z',
            }
            for row in rows
        ]
    }


def register_background_components(registry):
    """Register the expired-period query once per process."""
    registry.register(
        'capability_set_cooling_off_period_ed5144db.function.list_expired_cooling_periods',
        process_expired_cooling_periods,
    )
