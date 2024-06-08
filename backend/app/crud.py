from datetime import datetime
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas
from .security import get_password_hash, verify_password


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_file(db: Session, file: schemas.FileCreate, user_id: int):
    db_file = models.File(**file.dict(), owner_id=user_id)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_files(db: Session, user_id: int):
    files = db.query(models.File).filter(models.File.owner_id == user_id).all()
    return [file.filename for file in files]


def update_user(db: Session, user_id: int, updated_info: schemas.UserUpdate):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        for attr, value in updated_info.dict().items():
            setattr(user, attr, value)
        db.commit()
        db.refresh(user)
        return user
    return None


def change_password(db: Session, user_id: int, password_data: schemas.PasswordChange):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and verify_password(password_data.old_password, user.hashed_password):
        user.hashed_password = get_password_hash(password_data.new_password)
        db.commit()
        db.refresh(user)
        return user
    return None


def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False


def delete_file(db: Session, file_id: int, user_id: int):
    file = (
        db.query(models.File)
        .filter(models.File.id == file_id, models.File.owner_id == user_id)
        .first()
    )
    if file:
        db.delete(file)
        db.commit()
        return True
    return False


def rename_file(db: Session, file_id: int, new_filename: str, user_id: int):
    file = (
        db.query(models.File)
        .filter(models.File.id == file_id, models.File.owner_id == user_id)
        .first()
    )
    if file:
        file.filename = new_filename
        db.commit()
        db.refresh(file)
        return file
    return None


def search_files(db: Session, query: str, user_id: int):
    return (
        db.query(models.File)
        .filter(
            models.File.owner_id == user_id, models.File.filename.ilike(f"%{query}%")
        )
        .all()
    )


def filter_files(
    db: Session,
    file_type: Optional[str],
    min_size: Optional[int],
    max_size: Optional[int],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    user_id: int,
):
    query = db.query(models.File).filter(models.File.owner_id == user_id)
    if file_type:
        query = query.filter(models.File.file_type == file_type)
    if min_size:
        query = query.filter(models.File.size >= min_size)
    if max_size:
        query = query.filter(models.File.size <= max_size)
    if start_date:
        query = query.filter(models.File.created_at >= start_date)
    if end_date:
        query = query.filter(models.File.created_at <= end_date)
    return query.all()


def get_file_history(db: Session, file_id: int):
    return (
        db.query(models.FileHistory).filter(models.FileHistory.file_id == file_id).all()
    )


def user_activity_log(db: Session, user_id: int):
    return (
        db.query(models.UserActivityLog)
        .filter(models.UserActivityLog.user_id == user_id)
        .all()
    )


def usage_statistics(db: Session, user_id: int):
    total_uploads = (
        db.query(models.File).filter(models.File.owner_id == user_id).count()
    )
    total_storage_used = (
        db.query(func.sum(models.File.size))
        .filter(models.File.owner_id == user_id)
        .scalar()
        or 0
    )
    return {"total_uploads": total_uploads, "total_storage_used": total_storage_used}


# def generate_reports(db: Session, start_date: Optional[datetime], end_date: Optional[datetime], user_id: int):
#     # Implement your report generation logic here
#     pass
