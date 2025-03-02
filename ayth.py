from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
from database import get_db
from models import User, AuthToken
import secrets
from datetime import datetime, timedelta

auth_router = APIRouter()
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

def create_user(db: Session, username: str, password: str):
    hashed_password = pwd_context.hash(password)
    user = User(
        username=username,
        password_hash=hashed_password,
        updated_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    return user

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_token(user_id: int) -> str:
    token = secrets.token_hex(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    return token, expires_at


@auth_router.post("/register")
async def register(
        data: RegisterRequest,
        db: Session = Depends(get_db)
):
    # Проверка существующего пользователя
    existing_user = db.query(User).filter(User.username == data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Хеширование пароля
    hashed_password = pwd_context.hash(data.password)

    # Создание пользователя
    new_user = User(
        username=data.username,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()

    return {"message": "User registered successfully"}
@auth_router.post("/login")
def login(response: Response, data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token, expires_at = generate_token(user.id)
    db_token = AuthToken(user_id=user.id, token=token, expires_at=expires_at)
    db.add(db_token)
    db.commit()

    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=604800
    )
    return {"message": "Login successful"}


@auth_router.post("/logout")
def logout(response: Response, db: Session = Depends(get_db)):
    auth_token = response.cookies.get("auth_token")
    if auth_token:
        db.query(AuthToken).filter(AuthToken.token == auth_token).delete()
        db.commit()
    response.delete_cookie("auth_token")
    return {"message": "Logged out"}


@auth_router.get("/protected")
def protected_route(auth_token: str = Depends(lambda request: request.cookies.get("auth_token")),
                    db: Session = Depends(get_db)):
    if not auth_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token_record = db.query(AuthToken).filter(AuthToken.token == auth_token).first()
    if not token_record or token_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    return {"message": "You have access"}
