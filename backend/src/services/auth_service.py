"""
Authentication Service for WhatsApp RAG Assistant
"""
from datetime import datetime, timedelta
from typing import Optional
import uuid
from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from ..models.business import Business
from ..config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Secret key and algorithm
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)


def authenticate_business(db: Session, email: str, password: str) -> Optional[Business]:
    """Authenticate a business by email and password."""
    business = db.query(Business).filter(Business.email == email).first()
    if not business or not verify_password(password, business.hashed_password):
        return None
    return business


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_business(token: str, db: Session) -> Business:
    """Get the current business from the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    business = db.query(Business).filter(Business.email == email).first()
    if business is None:
        raise credentials_exception
    return business