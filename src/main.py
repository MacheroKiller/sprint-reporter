"""
Basic client for interacting with the Chaquén REST API.

This module provides helper functions to:

1. Authenticate a user and retrieve an access token.
2. Persist the authentication token in the .env file.
3. Retrieve authenticated user information.
4. Retrieve the user's projects.
5. Retrieve User Stories from the configured sprint.
"""

import os

import requests
from dotenv import load_dotenv, set_key


# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

# Load environment variables
load_dotenv()

# Environment file path
DOTENV_PATH = ".env"

# API base URL
BASE_URL = os.getenv("BASE_URL")

# Sprint slug prefix used to filter milestones
SPRINT_SLUG = "sprint-07-2026"


# -----------------------------------------------------------------------------
# API SERVICE
# -----------------------------------------------------------------------------

def service_request(method, endpoint, **kwargs):
    """
    Send an HTTP request to the Chaquén API.

    Args:
        method (str):
            HTTP method (GET, POST, PUT, DELETE, etc.).

        endpoint (str):
            API endpoint relative to BASE_URL.

        **kwargs:
            Additional arguments forwarded to requests.request(),
            such as json, params, data or files.

    Returns:
        dict | list:
            Parsed JSON response.

    Raises:
        Exception:
            If the request fails.
    """

    response = requests.request(
        method=method.upper(),
        url=BASE_URL + endpoint,
        headers=HEADERS,
        **kwargs,
    )

    if response.ok:
        return response.json()

    raise Exception(f"{response.status_code}: {response.text}")


# -----------------------------------------------------------------------------
# AUTHENTICATION
# -----------------------------------------------------------------------------

def get_auth_token():
    """
    Retrieve an authentication token.

    If a valid token is already stored in the .env file,
    it is reused. Otherwise, a new token is requested from
    the API, stored in the .env file and returned.

    Returns:
        str:
            Bearer authentication token.
    """

    # Reuse an existing token if available
    token = os.getenv("TOKEN")

    if token:
        return token

    # Authentication payload
    credentials = {
        "username": os.getenv("USERNAME"),
        "password": os.getenv("PASSWORD"),
        "type": "normal",
    }

    # Request a new token
    response = requests.post(BASE_URL + "auth", json=credentials)

    if not response.ok:
        raise Exception(f"{response.status_code}: {response.text}")

    token = response.json()["auth_token"]
    auth_token = f"Bearer {token}"

    # Persist token
    set_key(DOTENV_PATH, "TOKEN", auth_token)
    load_dotenv(DOTENV_PATH, override=True)

    return auth_token


# -----------------------------------------------------------------------------
# API QUERIES
# -----------------------------------------------------------------------------

def get_user_info():
    """
    Retrieve information about the authenticated user.

    Returns:
        dict:
            User information returned by the API.
    """

    print("Retrieving authenticated user information...")
    return service_request("GET", "users/me")


def get_user_projects(user_id):
    """
    Retrieve all projects associated with a user.

    Args:
        user_id (int):
            Authenticated user identifier.

    Returns:
        list[int]:
            List of project identifiers.
    """

    print("Retrieving user projects...")

    projects = service_request(
        "GET",
        f"projects?member={user_id}"
    )

    return [project["id"] for project in projects]


def get_user_story_ids(project_ids):
    """
    Retrieve the IDs of User Stories belonging to the
    configured sprint across all user's projects.

    Args:
        project_ids (list[int]):
            List of project identifiers.

    Returns:
        list[int]:
            User Story identifiers.
    """

    print("Retrieving sprint User Story IDs...")

    story_ids = []

    for project_id in project_ids:

        milestones = service_request(
            "GET",
            f"milestones?closed=false&project={project_id}"
        )

        filtered = [
            story["id"]
            for milestone in milestones
            if milestone["slug"].startswith(SPRINT_SLUG)
            for story in milestone["user_stories"]
        ]

        story_ids.extend(filtered)

    return story_ids


def get_user_stories(story_ids, user_id):
    """
    Retrieve User Stories assigned to the authenticated user.

    Args:
        story_ids (list[int]):
            User Story identifiers.

        user_id (int):
            Authenticated user identifier.

    Returns:
        list[dict]:
            User Stories assigned to the user.
    """

    print("Retrieving assigned User Stories...")

    user_stories = []

    for story_id in story_ids:

        story = service_request(
            "GET",
            f"userstories/{story_id}"
        )

        if user_id in story["assigned_users"]:
            user_stories.append(story)

    return user_stories


# -----------------------------------------------------------------------------
# EXECUTION
# -----------------------------------------------------------------------------

# Retrieve authentication token
auth_token = get_auth_token()

# Default request headers
HEADERS = {
    "Authorization": auth_token
}

# Retrieve authenticated user
user_id = get_user_info()["id"]

# Retrieve project IDs
project_ids = get_user_projects(user_id)

# Retrieve User Story IDs from the configured sprint
story_ids = get_user_story_ids(project_ids)

# Retrieve User Stories assigned to the authenticated user
user_stories = get_user_stories(story_ids, user_id)

print(f"Assigned User Stories: {len(user_stories)}")