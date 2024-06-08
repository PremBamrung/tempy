import os
import shutil
from datetime import datetime, timedelta
from typing import List, Optional

from app import crud, models, schemas, security
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqladmin import Admin, ModelView
from sqlalchemy.orm import Session

from . import crud
from .database import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()
# Initialize SQLAdmin and bind it to the app
admin = Admin(app, engine)
# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Load default user credentials
DEFAULT_USER_USERNAME = os.getenv("DEFAULT_USER_USERNAME")
DEFAULT_USER_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
FILE_STORAGE = "/app/storage"

os.makedirs(FILE_STORAGE, exist_ok=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Define admin views for User model
class UserAdmin(ModelView, model=models.User):
    column_list = ["id", "username", "email", "full_name", "disabled"]


# Define admin views for File model
class FileAdmin(ModelView, model=models.File):
    column_list = ["id", "filename", "owner"]


# Add UserAdmin and FileAdmin views to the SQLAdmin instance
admin.add_view(UserAdmin)
admin.add_view(FileAdmin)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Super Admin creation
def create_default_user():
    db = SessionLocal()
    try:
        if DEFAULT_USER_USERNAME and DEFAULT_USER_PASSWORD:
            if not crud.get_user_by_username(db, username=DEFAULT_USER_USERNAME):
                default_user = schemas.UserCreate(
                    username=DEFAULT_USER_USERNAME,
                    password=DEFAULT_USER_PASSWORD,
                    email=f"{DEFAULT_USER_USERNAME}@example.com",
                    full_name="Default User",
                )
                crud.create_user(db=db, user=default_user)
    finally:
        db.close()


# Call create_default_user function to create default user
@app.on_event("startup")
async def startup_event():
    # This code will run when the application starts up
    create_default_user()


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


# Endpoint to list users
@app.get("/users/", response_model=List[schemas.User])
async def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_users(db, skip=skip, limit=limit)


# Upload File
@app.post("/upload", response_model=schemas.File)
async def upload_file(
    file: UploadFile = File(...),
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_dir = os.path.join(FILE_STORAGE, current_user.username)
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    file_create = schemas.FileCreate(filename=file.filename)
    # Create file entry in the database
    new_file = crud.create_file(db=db, file=file_create, user_id=current_user.id)
    # Log user activity
    crud.create_user_activity_log(db=db, user_id=current_user.id, action=f"Uploaded file '{file.filename}'")
    return new_file

# Download File
@app.get("/download/{filename}")
async def download_file(
    filename: str, current_user: schemas.User = Depends(get_current_user),db: Session = Depends(get_db)
):
    user_dir = os.path.join(FILE_STORAGE, current_user.username)
    file_path = os.path.join(user_dir, filename)
    if os.path.exists(file_path):
        # Log user activity
        crud.create_user_activity_log(db=db, user_id=current_user.id, action=f"Downloaded file '{filename}'")
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")


@app.get("/filespace", response_model=schemas.Filespace)
async def check_filespace(
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    files = crud.get_files(db=db, user_id=current_user.id)
    total_size = sum(
        os.path.getsize(os.path.join(FILE_STORAGE, current_user.username, f))
        for f in files
    )
    return {"files": files, "total_size": total_size}


# Update User Information
@app.put("/users/{user_id}")
def update_user_info(
    user_id: int,
    updated_info: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    user = crud.update_user(db=db, user_id=user_id, updated_info=updated_info)
    if user:
        # Log user activity
        crud.create_user_activity_log(db=db, user_id=current_user.id, action="Updated user information")
        return user
    else:
        raise HTTPException(status_code=404, detail="User not found")


# Change Password
@app.put("/users/{user_id}/change-password")
def change_password(
    user_id: int,
    password_data: schemas.PasswordChange,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    user = crud.change_password(db=db, user_id=user_id, password_data=password_data)
    if user:
        # Log user activity
        crud.create_user_activity_log(db=db, user_id=current_user.id, action="Changed password")
        return user
    else:
        raise HTTPException(status_code=404, detail="User not found")


# Delete Account
@app.delete("/users/{user_id}")
def delete_account(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    success = crud.delete_user(db=db, user_id=user_id)
    if success:
        # Log user activity
        crud.create_user_activity_log(db=db, user_id=current_user.id, action="Deleted account")
        return {"message": "User deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="User not found")


# Delete File
@app.delete("/files/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    success = crud.delete_file(db=db, file_id=file_id, user_id=current_user.id)
    if success:
        # Log user activity
        crud.create_user_activity_log(db=db, user_id=current_user.id, action="Deleted file")
        return {"message": "File deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found")


# Rename File
@app.put("/files/{file_id}")
def rename_file(
    file_id: int,
    new_filename: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    file = crud.rename_file(
        db=db, file_id=file_id, new_filename=new_filename, user_id=current_user.id
    )
    if file:
        # Log user activity
        crud.create_user_activity_log(db=db, user_id=current_user.id, action=f"Renamed file '{new_filename}'")
        return file
    else:
        raise HTTPException(status_code=404, detail="File not found")

# Search Files
@app.get("/files/search")
def search_files(
    query: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    files = crud.search_files(db=db, query=query, user_id=current_user.id)
    return files


# Filter Files
@app.get("/files/filter")
def filter_files(
    file_type: Optional[str] = None,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    files = crud.filter_files(
        db=db,
        file_type=file_type,
        min_size=min_size,
        max_size=max_size,
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.id,
    )
    return files


# View File History
@app.get("/files/{file_id}/history")
def view_file_history(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    file_history = crud.get_file_history(db=db, file_id=file_id)
    return file_history


# User Activity Log
@app.get("/users/me/activity-log")
def user_activity_log(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    activity_log = crud.user_activity_log(db=db, user_id=current_user.id)
    return activity_log


# Usage Statistics
@app.get("/statistics")
def usage_statistics(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    statistics = crud.usage_statistics(db=db, user_id=current_user.id)
    return statistics


# # Generate Reports
# @app.get("/reports")
# def generate_reports(
#     start_date: Optional[datetime] = None,
#     end_date: Optional[datetime] = None,
#     db: Session = Depends(get_db),
#     current_user: schemas.User = Depends(get_current_user),
# ):
#     reports = crud.generate_reports(
#         db=db, start_date=start_date, end_date=end_date, user_id=current_user.id
#     )
#     return reports
