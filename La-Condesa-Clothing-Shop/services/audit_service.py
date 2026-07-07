import json
from datetime import datetime
from extensions import db
from models import AuditLog

class AuditService:

    def log(self, user_id=None, username=None, action=None, entity_type=None,
            entity_id=None, description=None, old_value=None, new_value=None,
            ip_address=None):
        if old_value is not None and not isinstance(old_value, str):
            old_value = json.dumps(old_value, ensure_ascii=False, default=str)
        if new_value is not None and not isinstance(new_value, str):
            new_value = json.dumps(new_value, ensure_ascii=False, default=str)

        log_entry = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry

    def get_logs(self, limit=100, offset=0, entity_type=None, action=None, user_id=None):
        query = AuditLog.query
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if action:
            query = query.filter(AuditLog.action == action)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    def get_logs_for_entity(self, entity_type, entity_id, limit=50):
        return AuditLog.query.filter_by(
            entity_type=entity_type,
            entity_id=entity_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()

    def count_logs(self, entity_type=None, action=None, user_id=None):
        query = AuditLog.query
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if action:
            query = query.filter(AuditLog.action == action)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        return query.count()

    def get_recent_activity(self, limit=20):
        return AuditLog.query.order_by(AuditLog.created_at.desc()).limit(limit).all()

audit_service = AuditService()
