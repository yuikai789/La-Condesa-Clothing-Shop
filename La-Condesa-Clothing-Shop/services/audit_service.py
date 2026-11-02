import json
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

    def count_logs(self, entity_type=None, action=None, user_id=None):
        query = AuditLog.query
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if action:
            query = query.filter(AuditLog.action == action)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        return query.count()


audit_service = AuditService()


def log_action(action, entity_type, entity_id, description, old_value=None, new_value=None):
    from flask import request
    from flask_login import current_user

    return audit_service.log(
        user_id=current_user.id,
        username=current_user.name,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        old_value=old_value,
        new_value=new_value,
        ip_address=request.remote_addr
    )
