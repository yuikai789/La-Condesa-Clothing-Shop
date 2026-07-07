from datetime import datetime
from extensions import db

class EmployeeProfile(db.Model):
    __tablename__ = 'employee_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    position = db.Column(db.String(100), nullable=True)
    hire_date = db.Column(db.Date, nullable=True)
    salary = db.Column(db.Float, nullable=True)
    emergency_contact = db.Column(db.String(100), nullable=True)
    emergency_phone = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('employee_profile', uselist=False, lazy='select'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'position': self.position,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'salary': self.salary,
            'emergency_contact': self.emergency_contact,
            'emergency_phone': self.emergency_phone,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<EmployeeProfile user#{self.user_id}>'
