from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

SECRET_KEY = 'CHANGE_THIS_SECRET_IN_PRODUCTION_AURALIX_2026'
ALGORITHM = 'HS256'
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')

def hash_password(password: str):
    return pwd_context.hash(password[:72])

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password[:72], hashed)

def create_token(user):
    return jwt.encode({'sub': str(user.id), 'exp': datetime.utcnow() + timedelta(hours=12)}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get('sub'))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(401, 'Invalid or expired token')
    user = db.get(User, user_id)
    if not user or not user.active:
        raise HTTPException(401, 'User is inactive')
    return user
