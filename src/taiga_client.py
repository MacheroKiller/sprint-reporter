"""
Client for interacting with the Taiga (Chaquén) REST API.

Encapsulates:

1. Authentication and access token persistence.
2. Retrieval of authenticated user information.
3. Retrieval of the user's projects.
4. Retrieval of User Stories from a given sprint.
"""

import os

import requests
from dotenv import load_dotenv, set_key


class TaigaClient:
    """
    Thin wrapper around the Taiga (Chaquén) REST API.

    Handles authentication (reusing/persisting the token in a .env file)
    and exposes convenience methods to fetch the User Stories assigned
    to the authenticated user within a given sprint.
    """

    def __init__(self, base_url=None, dotenv_path=".env"):
        """
        Args:
            base_url (str, optional):
                API base URL. Defaults to the BASE_URL environment
                variable.

            dotenv_path (str):
                Path to the .env file used to read credentials and
                persist the authentication token.
        """

        load_dotenv(dotenv_path)

        self.dotenv_path = dotenv_path
        self.base_url = base_url or os.getenv("BASE_URL")

        self.session = requests.Session()
        self.session.headers["Authorization"] = self._get_auth_token()

    # -------------------------------------------------------------------
    # AUTHENTICATION
    # -------------------------------------------------------------------

    def _get_auth_token(self):
        """
        Retrieve an authentication token.

        If a valid token is already stored in the .env file, it is
        reused. Otherwise, a new token is requested from the API,
        persisted in the .env file and returned.

        Returns:
            str:
                Bearer authentication token.
        """

        token = os.getenv("TOKEN")

        if token:
            return token

        credentials = {
            "username": os.getenv("USERNAME"),
            "password": os.getenv("PASSWORD"),
            "type": "normal",
        }

        response = requests.post(self.base_url + "auth", json=credentials)

        if not response.ok:
            raise Exception(f"{response.status_code}: {response.text}")

        raw_token = response.json()["auth_token"]
        auth_token = f"Bearer {raw_token}"

        set_key(self.dotenv_path, "TOKEN", auth_token)
        load_dotenv(self.dotenv_path, override=True)

        return auth_token

    # -------------------------------------------------------------------
    # LOW-LEVEL REQUEST HELPER
    # -------------------------------------------------------------------

    def _request(self, method, endpoint, **kwargs):
        """
        Send an HTTP request to the Taiga API.

        Args:
            method (str):
                HTTP method (GET, POST, PUT, DELETE, etc.).

            endpoint (str):
                API endpoint relative to base_url.

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

        response = self.session.request(
            method=method.upper(),
            url=self.base_url + endpoint,
            **kwargs,
        )

        if response.ok:
            return response.json()

        raise Exception(f"{response.status_code}: {response.text}")

    # -------------------------------------------------------------------
    # API QUERIES
    # -------------------------------------------------------------------

    def get_current_user(self):
        """
        Retrieve information about the authenticated user.

        Returns:
            dict:
                User information returned by the API.
        """

        print("Retrieving authenticated user information...")
        return self._request("GET", "users/me")

    def get_user_projects(self, user_id):
        """
        Retrieve all project IDs associated with a user.

        Args:
            user_id (int):
                Authenticated user identifier.

        Returns:
            list[int]:
                List of project identifiers.
        """

        print("Retrieving user projects...")

        projects = self._request("GET", f"projects?member={user_id}")

        return [project["id"] for project in projects]

    def get_sprint_user_story_ids(self, project_ids, sprint_slug):
        """
        Retrieve the IDs of User Stories belonging to the given sprint
        across a list of projects.

        Args:
            project_ids (list[int]):
                List of project identifiers.

            sprint_slug (str):
                Sprint slug prefix used to filter milestones.

        Returns:
            list[int]:
                User Story identifiers.
        """

        print("Retrieving sprint User Story IDs...")

        story_ids = []

        for project_id in project_ids:
            milestones = self._request(
                "GET", f"milestones?closed=false&project={project_id}"
            )

            filtered = [
                story["id"]
                for milestone in milestones
                if milestone["slug"].startswith(sprint_slug)
                for story in milestone["user_stories"]
            ]

            story_ids.extend(filtered)

        return story_ids

    def get_assigned_user_stories(self, story_ids, user_id):
        """
        Retrieve, among the given User Stories, those assigned to the
        authenticated user.

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

        assigned_stories = []

        for story_id in story_ids:
            story = self._request("GET", f"userstories/{story_id}")

            if user_id in story["assigned_users"]:
                assigned_stories.append(story)

        return assigned_stories

    # -------------------------------------------------------------------
    # HIGH-LEVEL WORKFLOW
    # -------------------------------------------------------------------

    def get_my_sprint_stories(self, sprint_slug):
        """
        Convenience method that runs the full workflow: resolve the
        authenticated user, their projects, the User Stories in the
        given sprint, and filter those assigned to the user.

        Args:
            sprint_slug (str):
                Sprint slug prefix used to filter milestones.

        Returns:
            list[dict]:
                User Stories assigned to the authenticated user.
        """

        user_id = self.get_current_user()["id"]
        project_ids = self.get_user_projects(user_id)
        story_ids = self.get_sprint_user_story_ids(project_ids, sprint_slug)

        return self.get_assigned_user_stories(story_ids, user_id)
