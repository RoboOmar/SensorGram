from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.robot import Robot

ALGORITHM = "HS256"


# ── Password helpers (using bcrypt directly — passlib 1.7.4 is incompatible with bcrypt 5.x) ──

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ── DB lookups ────────────────────────────────────────────────────────────────

def get_robot_by_username(db: Session, username: str) -> Optional[Robot]:
    return db.query(Robot).filter(Robot.username == username).first()

def get_robot_by_email(db: Session, email: str) -> Optional[Robot]:
    return db.query(Robot).filter(Robot.email == email).first()


def get_robot_by_api_key(db: Session, api_key: str) -> Optional[Robot]:
    return db.query(Robot).filter(Robot.api_key == api_key).first()


def authenticate_robot(db: Session, identifier: str, password: str) -> Optional[Robot]:
    if "@" in identifier:
        robot = get_robot_by_email(db, identifier)
    else:
        robot = get_robot_by_username(db, identifier)

    if robot and verify_password(password, robot.hashed_password):
        return robot
    return None
