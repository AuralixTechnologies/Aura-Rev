from .database import Base, engine, SessionLocal
from .models import User
from .auth import hash_password

Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()
    users = [
        ('Admin User', 'admin@auralix.org', '8531008601', 'Admin@123', 'Admin'),
        ('Person 2', 'user2@auralix.org', '', 'User@123', 'Staff'),
        ('Person 3', 'user3@auralix.org', '', 'User@123', 'Staff'),
    ]
    for name, email, phone, pwd, role in users:
        if not db.query(User).filter_by(email=email).first():
            db.add(User(name=name, email=email, phone=phone, password_hash=hash_password(pwd), role=role))
    db.commit()
    db.close()
    print('Auralix database ready. 3 users created/verified.')

if __name__ == '__main__':
    seed()
