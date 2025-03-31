from sqlalchemy.orm import Session
from api.auth.schema import User
from passlib.context import CryptContext
import api.models as md
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from api.db import get_db
from api.config import settings
from api.auth.dependencies import oauth2_scheme


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def get_by_username(db: Session, username: str) -> User | None:
    return db.query(md.User).filter(md.User.username == username).first()


async def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> md.User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username = payload.get("sub")
        if not username:
            return None
    except JWTError:
        return None

    user = db.query(md.User).filter(md.User.username == username).first()
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> md.User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    username = payload.get("sub")

    user = db.query(md.User).filter(md.User.username == username).first()
    return user