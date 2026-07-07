from datetime import datetime
from flask import session, request
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)

def track_session_activity():
    if current_user.is_authenticated:
        session['last_activity'] = datetime.utcnow().isoformat()
        session['user_agent'] = request.headers.get('User-Agent')
        session['ip_address'] = request.remote_addr


def cleanup_expired_sessions():
    logger.info("Session cleanup task executed")
