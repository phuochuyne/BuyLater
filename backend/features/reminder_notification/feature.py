import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps

from backend.core.db import get_engine

bp = Blueprint('capability_reminder_notification_fd8968f7', __name__)


def get_db():
    """Return the shared environment-configured database engine."""
    return get_engine()


def require_auth(f):
    """Authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'unauthorized', 'message': 'Authentication required'}), 401
        
        # Extract user_id from token (simplified - in production use proper JWT validation)
        try:
            token = auth_header.replace('Bearer ', '')
            # Store user_id in g for access in route handlers
            # In production, validate JWT and extract user_id
            g.user_id = token  # Simplified: assuming token is user_id
        except Exception:
            return jsonify({'error': 'unauthorized', 'message': 'Authentication required'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/api/capability_reminder_notification_fd8968f7/notifications/schedule', methods=['POST'])
@require_auth
def schedule_notification():
    """Creates a scheduled notification record when an item is saved with a cooling-off period"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'item_id', 'scheduled_for', 'notification_title', 
                          'notification_body', 'deep_link_target']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': 'invalid_request',
                'message': 'Missing or invalid required fields'
            }), 400
        
        # Validate field constraints
        if not data.get('notification_title') or len(data['notification_title']) > 100 or len(data['notification_title']) < 1:
            return jsonify({
                'error': 'invalid_request',
                'message': 'Missing or invalid required fields'
            }), 400
        
        if not data.get('notification_body') or len(data['notification_body']) > 200 or len(data['notification_body']) < 1:
            return jsonify({
                'error': 'invalid_request',
                'message': 'Missing or invalid required fields'
            }), 400
        
        if not data.get('deep_link_target') or len(data['deep_link_target']) > 500 or len(data['deep_link_target']) < 1:
            return jsonify({
                'error': 'invalid_request',
                'message': 'Missing or invalid required fields'
            }), 400
        
        # Validate UUID formats
        try:
            uuid.UUID(data['user_id'])
            uuid.UUID(data['item_id'])
        except (ValueError, AttributeError):
            return jsonify({
                'error': 'invalid_request',
                'message': 'Missing or invalid required fields'
            }), 400
        
        # Validate datetime format
        try:
            scheduled_for = datetime.fromisoformat(data['scheduled_for'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return jsonify({
                'error': 'invalid_request',
                'message': 'Missing or invalid required fields'
            }), 400
        
        # Generate notification ID
        notification_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        # Insert into database
        db = get_db()
        query = text("""
            INSERT INTO f_fd8968f7__scheduled_notifications 
            (id, item_id, user_id, scheduled_for, status, notification_title, 
             notification_body, deep_link_target, created_at)
            VALUES (:id, :item_id, :user_id, :scheduled_for, :status, :notification_title,
                    :notification_body, :deep_link_target, :created_at)
        """)
        
        with db.connect() as conn:
            conn.execute(query, {
                'id': notification_id,
                'item_id': data['item_id'],
                'user_id': data['user_id'],
                'scheduled_for': scheduled_for,
                'status': 'pending',
                'notification_title': data['notification_title'],
                'notification_body': data['notification_body'],
                'deep_link_target': data['deep_link_target'],
                'created_at': created_at
            })
            conn.commit()
        
        return jsonify({
            'id': notification_id,
            'status': 'pending',
            'scheduled_for': scheduled_for.isoformat()
        }), 201
        
    except SQLAlchemyError:
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to schedule notification'
        }), 500
    except Exception:
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to schedule notification'
        }), 500


def process_due_notifications():
    """Background job that processes pending notifications with scheduled_for time in the past"""
    try:
        db = get_db()
        current_time = datetime.utcnow()
        
        # Find all pending notifications that are due
        select_query = text("""
            SELECT id, user_id, notification_title, notification_body, deep_link_target, item_id
            FROM f_fd8968f7__scheduled_notifications
            WHERE status = 'pending' AND scheduled_for <= :current_time
        """)
        
        with db.connect() as conn:
            result = conn.execute(select_query, {'current_time': current_time})
            due_notifications = result.fetchall()
            
            for notification in due_notifications:
                notification_id = notification[0]
                user_id = notification[1]
                title = notification[2]
                body = notification[3]
                deep_link = notification[4]
                item_id = notification[5]
                
                try:
                    # Send push notification (mock implementation)
                    # In production, integrate with actual push notification service
                    send_push_notification(user_id, title, body, deep_link)
                    
                    # Update status to sent
                    update_query = text("""
                        UPDATE f_fd8968f7__scheduled_notifications
                        SET status = 'sent', sent_at = :sent_at
                        WHERE id = :id
                    """)
                    conn.execute(update_query, {
                        'id': notification_id,
                        'sent_at': datetime.utcnow()
                    })
                    
                except Exception:
                    # Mark as failed if push notification fails
                    update_query = text("""
                        UPDATE f_fd8968f7__scheduled_notifications
                        SET status = 'failed'
                        WHERE id = :id
                    """)
                    conn.execute(update_query, {'id': notification_id})
            
            conn.commit()
        
        return {'processed': len(due_notifications)}
        
    except Exception as e:
        # Log error but don't raise - background jobs should be resilient
        return {'error': str(e)}


def send_push_notification(user_id, title, body, deep_link):
    """Mock function to send push notification - integrate with actual service in production"""
    # In production, this would call Firebase Cloud Messaging, APNs, or similar service
    pass


@bp.route('/api/capability_reminder_notification_fd8968f7/notifications/<notification_id>/cancel', methods=['PATCH'])
@require_auth
def cancel_notification(notification_id):
    """Cancels a pending notification when a user acts on an item before the cooling-off period expires"""
    try:
        # Validate UUID format
        try:
            uuid.UUID(notification_id)
        except ValueError:
            return jsonify({
                'error': 'not_found',
                'message': 'Notification not found'
            }), 404
        
        db = get_db()
        
        # Check if notification exists and get its status
        select_query = text("""
            SELECT status FROM f_fd8968f7__scheduled_notifications
            WHERE id = :id
        """)
        
        with db.connect() as conn:
            result = conn.execute(select_query, {'id': notification_id})
            row = result.fetchone()
            
            if not row:
                return jsonify({
                    'error': 'not_found',
                    'message': 'Notification not found'
                }), 404
            
            current_status = row[0]
            
            if current_status == 'sent':
                return jsonify({
                    'error': 'already_sent',
                    'message': 'Cannot cancel notification that has already been sent'
                }), 409
            
            # Update status to cancelled
            update_query = text("""
                UPDATE f_fd8968f7__scheduled_notifications
                SET status = 'cancelled'
                WHERE id = :id
            """)
            conn.execute(update_query, {'id': notification_id})
            conn.commit()
        
        return jsonify({
            'id': notification_id,
            'status': 'cancelled'
        }), 200
        
    except SQLAlchemyError:
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to cancel notification'
        }), 500


@bp.route('/api/capability_reminder_notification_fd8968f7/notifications/<notification_id>', methods=['GET'])
@require_auth
def get_notification_status(notification_id):
    """Retrieves the current status and details of a scheduled notification"""
    try:
        # Validate UUID format
        try:
            uuid.UUID(notification_id)
        except ValueError:
            return jsonify({
                'error': 'not_found',
                'message': 'Notification not found'
            }), 404
        
        db = get_db()
        
        # Retrieve notification details
        query = text("""
            SELECT id, user_id, item_id, scheduled_for, status, sent_at, created_at
            FROM f_fd8968f7__scheduled_notifications
            WHERE id = :id
        """)
        
        with db.connect() as conn:
            result = conn.execute(query, {'id': notification_id})
            row = result.fetchone()
            
            if not row:
                return jsonify({
                    'error': 'not_found',
                    'message': 'Notification not found'
                }), 404
            
            response = {
                'id': row[0],
                'user_id': row[1],
                'item_id': row[2],
                'scheduled_for': row[3].isoformat() if row[3] else None,
                'status': row[4],
                'sent_at': row[5].isoformat() if row[5] else None,
                'created_at': row[6].isoformat() if row[6] else None
            }
            
            return jsonify(response), 200
        
    except SQLAlchemyError:
        return jsonify({
            'error': 'internal_error',
            'message': 'Failed to retrieve notification'
        }), 500


def register_background_components(registry):
    """Register the due-notification processor once per process."""
    registry.register(
        'capability_reminder_notification_fd8968f7.function.process_due_notifications',
        process_due_notifications,
    )
