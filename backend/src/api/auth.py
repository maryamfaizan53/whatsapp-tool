"""
Authentication API Endpoints for WhatsApp RAG Assistant
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.business import Business
from ..services.auth_service import (
    authenticate_business,
    create_access_token,
    get_password_hash
)
from ..schemas.auth import BusinessCreate, Token, BusinessResponse
from ..config import settings

router = APIRouter()


@router.post("/register", response_model=BusinessResponse)
def register_business(business_data: BusinessCreate, db: Session = Depends(get_db)):
    """Register a new business."""
    # Check if business with this email already exists
    existing_business = db.query(Business).filter(Business.email == business_data.email).first()
    if existing_business:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new business
    hashed_password = get_password_hash(business_data.password)
    new_business = Business(
        name=business_data.name,
        email=business_data.email,
        hashed_password=hashed_password
    )

    db.add(new_business)
    db.commit()
    db.refresh(new_business)

    return BusinessResponse(
        business_id=str(new_business.business_id),
        name=new_business.name,
        email=new_business.email
    )


@router.post("/login", response_model=Token)
def login_business(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login a business and return access token."""
    business = authenticate_business(
        db, form_data.username, form_data.password
    )
    if not business:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": business.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}