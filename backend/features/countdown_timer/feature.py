from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta, timezone

countdown_timer_bp = Blueprint('countdown_timer', __name__, url_prefix='/api/countdown-timer')


@countdown_timer_bp.route('/calculate', methods=['POST'])
def calculate_countdown():
    """
    Calculate the remaining time in a cooling-off period.

    Expected JSON payload:
    {
        "start_time": "2024-01-01T10:00:00Z",  # ISO 8601 format
        "duration_seconds": 3600  # Duration of cooling-off period in seconds
    }

    Returns:
    {
        "remaining_seconds": 1800,
        "total_seconds": 3600,
        "percentage_remaining": 50.0,
        "is_expired": false,
        "start_time": "2024-01-01T10:00:00Z",
        "end_time": "2024-01-01T11:00:00Z",
        "current_time": "2024-01-01T10:30:00Z"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'error': 'Request body must be JSON',
                'message': 'Invalid request format'
            }), 400

        start_time_str = data.get('start_time')
        duration_seconds = data.get('duration_seconds')

        if not start_time_str:
            return jsonify({
                'error': 'Missing required field',
                'message': 'start_time is required'
            }), 400

        if duration_seconds is None:
            return jsonify({
                'error': 'Missing required field',
                'message': 'duration_seconds is required'
            }), 400

        try:
            duration_seconds = int(duration_seconds)
            if duration_seconds < 0:
                return jsonify({
                    'error': 'Invalid duration',
                    'message': 'duration_seconds must be non-negative'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'error': 'Invalid duration',
                'message': 'duration_seconds must be a valid integer'
            }), 400

        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return jsonify({
                'error': 'Invalid timestamp',
                'message': 'start_time must be in ISO 8601 format'
            }), 400

        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        else:
            start_time = start_time.astimezone(timezone.utc)
        current_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(seconds=duration_seconds)

        elapsed_seconds = (current_time - start_time).total_seconds()
        remaining_seconds = max(0, duration_seconds - elapsed_seconds)

        is_expired = current_time >= end_time
        percentage_remaining = (remaining_seconds / duration_seconds * 100) if duration_seconds > 0 else 0

        return jsonify({
            'remaining_seconds': int(remaining_seconds),
            'total_seconds': duration_seconds,
            'percentage_remaining': round(percentage_remaining, 2),
            'is_expired': is_expired,
            'start_time': start_time.isoformat().replace('+00:00', 'Z'),
            'end_time': end_time.isoformat().replace('+00:00', 'Z'),
            'current_time': current_time.isoformat().replace('+00:00', 'Z')
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@countdown_timer_bp.route('/status', methods=['GET'])
def get_countdown_status():
    """
    Get countdown status based on query parameters.

    Query parameters:
    - start_time: ISO 8601 timestamp
    - duration_seconds: Duration in seconds

    Returns the same format as calculate_countdown
    """
    try:
        start_time_str = request.args.get('start_time')
        duration_seconds_str = request.args.get('duration_seconds')

        if not start_time_str:
            return jsonify({
                'error': 'Missing required parameter',
                'message': 'start_time query parameter is required'
            }), 400

        if not duration_seconds_str:
            return jsonify({
                'error': 'Missing required parameter',
                'message': 'duration_seconds query parameter is required'
            }), 400

        try:
            duration_seconds = int(duration_seconds_str)
            if duration_seconds < 0:
                return jsonify({
                    'error': 'Invalid duration',
                    'message': 'duration_seconds must be non-negative'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'error': 'Invalid duration',
                'message': 'duration_seconds must be a valid integer'
            }), 400

        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return jsonify({
                'error': 'Invalid timestamp',
                'message': 'start_time must be in ISO 8601 format'
            }), 400

        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        else:
            start_time = start_time.astimezone(timezone.utc)
        current_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(seconds=duration_seconds)

        elapsed_seconds = (current_time - start_time).total_seconds()
        remaining_seconds = max(0, duration_seconds - elapsed_seconds)

        is_expired = current_time >= end_time
        percentage_remaining = (remaining_seconds / duration_seconds * 100) if duration_seconds > 0 else 0

        return jsonify({
            'remaining_seconds': int(remaining_seconds),
            'total_seconds': duration_seconds,
            'percentage_remaining': round(percentage_remaining, 2),
            'is_expired': is_expired,
            'start_time': start_time.isoformat().replace('+00:00', 'Z'),
            'end_time': end_time.isoformat().replace('+00:00', 'Z'),
            'current_time': current_time.isoformat().replace('+00:00', 'Z')
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@countdown_timer_bp.route('/format', methods=['POST'])
def format_countdown_time():
    """
    Format remaining seconds into human-readable format.

    Expected JSON payload:
    {
        "seconds": 3665
    }

    Returns:
    {
        "seconds": 3665,
        "formatted": "1h 1m 5s",
        "hours": 1,
        "minutes": 1,
        "seconds_remaining": 5,
        "days": 0
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'error': 'Request body must be JSON',
                'message': 'Invalid request format'
            }), 400

        seconds = data.get('seconds')

        if seconds is None:
            return jsonify({
                'error': 'Missing required field',
                'message': 'seconds is required'
            }), 400

        try:
            seconds = int(seconds)
            if seconds < 0:
                return jsonify({
                    'error': 'Invalid value',
                    'message': 'seconds must be non-negative'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'error': 'Invalid value',
                'message': 'seconds must be a valid integer'
            }), 400

        days = seconds // 86400
        remaining = seconds % 86400
        hours = remaining // 3600
        remaining = remaining % 3600
        minutes = remaining // 60
        seconds_remaining = remaining % 60

        formatted_parts = []
        if days > 0:
            formatted_parts.append(f"{days}d")
        if hours > 0:
            formatted_parts.append(f"{hours}h")
        if minutes > 0:
            formatted_parts.append(f"{minutes}m")
        if seconds_remaining > 0 or not formatted_parts:
            formatted_parts.append(f"{seconds_remaining}s")

        formatted = " ".join(formatted_parts)

        return jsonify({
            'seconds': seconds,
            'formatted': formatted,
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'seconds_remaining': seconds_remaining
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@countdown_timer_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for the countdown timer service.
    """
    return jsonify({
        'status': 'healthy',
        'service': 'countdown_timer',
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }), 200


def register_blueprint(app):
    """
    Register the countdown timer blueprint with the Flask app.
    """
    app.register_blueprint(countdown_timer_bp)
