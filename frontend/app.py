import os

import requests
import streamlit as st

API_URL = "http://backend:8000"

st.title("File Management App")

if "token" not in st.session_state:
    st.session_state.token = None
# Initialize session state if not already initialized
if "username" not in st.session_state:
    st.session_state.username = None


def login():
    st.session_state.token = (
        requests.post(
            f"{API_URL}/token",
            data={
                "username": st.session_state.username,
                "password": st.session_state.password,
            },
        )
        .json()
        .get("access_token")
    )


def logout():
    st.session_state.token = None


if st.session_state.token:
    st.sidebar.button("Logout", on_click=logout)
    st.write("Logged in as", st.session_state.username)

    st.subheader("Upload a file")
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        files = {"file": uploaded_file.getvalue()}
        response = requests.post(
            f"{API_URL}/upload",
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            files=files,
        )
        st.write(response.json())

    st.subheader("Check available files and space")
    response = requests.get(
        f"{API_URL}/filespace",
        headers={"Authorization": f"Bearer {st.session_state.token}"},
    )
    data = response.json()
    st.write("Files:", data["files"])
    st.write("Total size:", data["total_size"], "bytes")
else:
    st.subheader("Login")
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    st.button("Login", on_click=login)
