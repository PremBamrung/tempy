import os
import shutil

import pytest
import requests
from dotenv import load_dotenv

load_dotenv("backend/.env")

# Mocking environment variables
DEFAULT_USER_USERNAME = os.getenv("DEFAULT_USER_USERNAME")
DEFAULT_USER_PASSWORD = os.getenv("DEFAULT_USER_PASSWORD")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")

# Base URL for the API
API_URL = "http://localhost:8000"


@pytest.fixture
def access_token():
    # Login to get access token
    login_data = {
        "username": DEFAULT_USER_USERNAME,
        "password": DEFAULT_USER_PASSWORD,
    }
    response = requests.post(f"{API_URL}/token", data=login_data)
    response_data = response.json()
    assert response.status_code == 200
    assert "access_token" in response_data
    return response_data["access_token"]


def test_create_user(access_token):
    # Test successful user creation
    user_data = {
        "username": "new_user",
        "password": "new_password",
        "email": "new_user@example.com",
        "full_name": "New User",
    }
    response = requests.post(f"{API_URL}/users/", json=user_data)
    assert response.status_code == 200
    assert response.json()["username"] == user_data["username"]

    # Test duplicate username
    response = requests.post(f"{API_URL}/users/", json=user_data)
    assert response.status_code == 400


@pytest.mark.dependency()
def test_upload_file(access_token):
    # Upload a file
    files = {"file": ("test_file.txt", "Test content")}
    response = requests.post(
        f"{API_URL}/upload",
        files=files,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    return response.json()["id"]


@pytest.mark.dependency(depends=["test_upload_file"])
def test_download_file(access_token, upload_file):
    # Download the uploaded file
    response = requests.get(
        f"{API_URL}/download/{upload_file}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.content == b"Test content"

    # Cleanup
    response = requests.delete(
        f"{API_URL}/files/{upload_file}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200


def test_check_filespace(access_token):
    # Check filespace
    response = requests.get(
        f"{API_URL}/filespace", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert "files" in response.json()
    assert "total_size" in response.json()
