# Tempy : Temporary File Storage in Python

This is a simple file management application that allows users to upload and download temporary files from any terminal using `curl` or `wget`. The backend is built using FastAPI with SQLAlchemy for database management, and the frontend is built using Streamlit. The application supports user authentication and each user has their own directory on the server.

## Features

- User registration and authentication
- File upload and download
- File space checking for each user
- Streamlit frontend for user interaction
- Backend API with FastAPI
- SQLite database with SQLAlchemy
- Dockerized using Docker Compose

## Project Structure

```
project/
│
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── crud.py
│   ├── database.py
│   ├── security.py
│   ├── schemas.py
│   ├── Dockerfile
│   └── .env
│
├── frontend/
│   ├── app.py
│   ├── Dockerfile
│   └── .env
│
├── docker-compose.yml
└── .env
```

## Installation

### Prerequisites

- Docker
- Docker Compose

### Steps

1. Clone the repository:

    ```sh
    git clone https://github.com/yourusername/file-management-app.git
    cd file-management-app
    ```

2. Create a `.env` file in the root directory and add the following environment variables:

    ```env
    SECRET_KEY=your-secret-key
    SUPER_ADMIN_USERNAME=admin
    SUPER_ADMIN_PASSWORD=adminpassword
    ```

3. Navigate to the backend directory and create a `.env` file with the following content:

    ```env
    SECRET_KEY=your-secret-key
    SUPER_ADMIN_USERNAME=admin
    SUPER_ADMIN_PASSWORD=adminpassword
    ```

4. Navigate to the frontend directory and create a `.env` file with the following content:

    ```env
    API_URL=http://backend:8000
    ```

5. Build and start the application using Docker Compose:

    ```sh
    docker-compose up --build
    ```

## Usage

### Access the Frontend

- Open your browser and navigate to `http://localhost:8501` to access the Streamlit frontend.

### Using the API

#### Register a new user

```sh
curl -X POST "http://localhost:8000/users/" -H "Content-Type: application/json" -d '{"username": "testuser", "email": "testuser@example.com", "full_name": "Test User", "password": "testpassword"}'
```

#### Login and get token

```sh
curl -X POST "http://localhost:8000/token" -d "username=testuser&password=testpassword"
```

#### Upload a file

```sh
curl -X POST "http://localhost:8000/upload" -H "Authorization: Bearer <your_token>" -F "file=@<path_to_your_file>"
```

#### Download a file

```sh
curl -X GET "http://localhost:8000/download/<filename>" -H "Authorization: Bearer <your_token>" -O
```

#### Check file space

```sh
curl -X GET "http://localhost:8000/filespace" -H "Authorization: Bearer <your_token>"
```

## API Endpoints

- `POST /users/`: Register a new user
- `POST /token`: Obtain a JWT token
- `POST /upload`: Upload a file
- `GET /download/{filename}`: Download a file
- `GET /filespace`: Check available file space and list files

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [Streamlit](https://streamlit.io/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Docker](https://www.docker.com/)

---

