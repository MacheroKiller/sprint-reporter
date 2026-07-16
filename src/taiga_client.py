"""
Client for interacting with the Taiga (Chaquén) REST API.

This module provides a lightweight wrapper around the Taiga REST API,
handling authentication and exposing helper methods to retrieve the
authenticated user's projects and assigned User Stories for a specific
sprint.
"""

import os
import re

import requests
from dotenv import load_dotenv


class TaigaClient:
    """
    Lightweight client for the Taiga (Chaquén) REST API.

    The client manages authentication and provides convenience methods
    for retrieving the authenticated user's assigned User Stories within
    a given sprint.

    Authentication is performed using username and password credentials.
    Once authenticated, all subsequent requests reuse the same HTTP
    session.
    """

    def __init__(self, base_url=None, dotenv_path=".env"):
        """
        Initialize the API client.

        Args:
            base_url (str, optional):
                Base URL of the Taiga REST API. If omitted, the value of
                the ``TAIGA_URL`` environment variable is used.

            dotenv_path (str, optional):
                Path to the ``.env`` file containing the application
                configuration.

        Raises:
            ValueError:
                If no base URL is provided and the ``TAIGA_URL``
                environment variable is not defined.
        """

        load_dotenv(dotenv_path)

        self.dotenv_path = dotenv_path
        self.base_url = base_url or os.getenv("TAIGA_URL")

        if not self.base_url:
            raise ValueError(
                "TAIGA_URL is not configured. Define it in the .env "
                "file or provide the base_url argument."
            )

        self.session = requests.Session()
        self.session.headers["Authorization"] = ""

        # Matches sprint slugs such as:
        # sprint-6-2026
        # sprint-06-2026
        # sprint-0006-2026
        self.sprint_slug_pattern = re.compile(r"^sprint-0*(\d+)-(\d{4})")

    def _get_auth_token(self, username, password):
        """
        Authenticate against the Taiga API.

        The authentication token returned by the API is stored in the
        current HTTP session and automatically included in subsequent
        requests.

        Args:
            username (str):
                Taiga username or email.

            password (str):
                Taiga password.

        Returns:
            str:
                Bearer authentication token.

        Raises:
            Exception:
                If authentication fails.
        """

        credentials = {
            "username": username,
            "password": password,
            "type": "normal",
        }

        response = requests.post(
            self.base_url + "auth",
            json=credentials,
        )

        if not response.ok:
            raise Exception(f"{response.status_code}: {response.text}")

        raw_token = response.json()["auth_token"]
        auth_token = f"Bearer {raw_token}"

        self.session.headers["Authorization"] = auth_token

        return auth_token

    def _request(self, method, endpoint, **kwargs):
        """
        Execute an HTTP request against the Taiga API.

        This helper automatically prefixes the endpoint with the
        configured base URL and reuses the authenticated HTTP session.

        Args:
            method (str):
                HTTP method.

            endpoint (str):
                API endpoint relative to the configured base URL.

            **kwargs:
                Additional keyword arguments forwarded to
                ``requests.Session.request``.

        Returns:
            dict | list:
                Parsed JSON response.

        Raises:
            Exception:
                If the request is unsuccessful.
        """

        response = self.session.request(
            method=method.upper(),
            url=self.base_url + endpoint,
            **kwargs,
        )

        if response.ok:
            return response.json()

        raise Exception(f"{response.status_code}: {response.text}")

    def get_current_user(self):
        """
        Retrieve information about the authenticated user.

        Returns:
            dict:
                User information returned by the API.

        Raises:
            Exception:
                If the request fails.
        """

        print("Retrieving authenticated user information...")

        return self._request("GET", "users/me")

    def get_user_projects(self, user_id):
        """
        Retrieve the projects associated with a user.

        Args:
            user_id (int):
                Authenticated user identifier.

        Returns:
            list[int]:
                Project identifiers.

        Raises:
            Exception:
                If the request fails.
        """

        print("Retrieving user projects...")

        projects = self._request(
            "GET",
            f"projects?member={user_id}",
        )

        return [project["id"] for project in projects]

    def get_sprint_user_story_ids(
        self,
        project_ids,
        sprint_number,
        sprint_year,
    ):
        """
        Retrieve the User Story IDs belonging to a sprint.

        The sprint is searched across every project provided.

        Args:
            project_ids (list[int]):
                Project identifiers.

            sprint_number (int):
                Sprint number.

            sprint_year (int):
                Sprint year.

        Returns:
            list[int]:
                User Story identifiers that belong to the requested
                sprint.

        Raises:
            Exception:
                If any API request fails.
        """

        print("Retrieving sprint User Story IDs...")

        story_ids = []

        for project_id in project_ids:
            milestones = self._request(
                "GET",
                f"milestones?closed=false&project={project_id}",
            )

            filtered = [
                story["id"]
                for milestone in milestones
                if self._matches_sprint(milestone["slug"], sprint_number, sprint_year)
                for story in milestone["user_stories"]
            ]

            story_ids.extend(filtered)

        return story_ids

    def _matches_sprint(
        self,
        milestone_slug,
        sprint_number,
        sprint_year,
    ):
        """
        Determine whether a milestone slug matches the requested sprint.

        Leading zeros in the sprint number are ignored. Therefore,
        ``sprint-6-2026`` and ``sprint-06-2026`` are treated as
        equivalent.

        Args:
            milestone_slug (str):
                Milestone slug returned by the API.

            sprint_number (int):
                Expected sprint number.

            sprint_year (int):
                Expected sprint year.

        Returns:
            bool:
                True if the milestone corresponds to the requested
                sprint; otherwise False.
        """

        match = self.sprint_slug_pattern.match(milestone_slug)

        if not match:
            return False

        number, year = match.groups()

        return int(number) == sprint_number and int(year) == sprint_year

    def get_assigned_user_stories(self, story_ids, user_id):
        """
        Retrieve the User Stories assigned to the authenticated user.

        Args:
            story_ids (list[int]):
                User Story identifiers.

            user_id (int):
                Authenticated user identifier.

        Returns:
            list[dict]:
                Assigned User Stories. Each dictionary contains the
                story ID, reference number, subject and description.

        Raises:
            Exception:
                If any API request fails.
        """

        print("Retrieving assigned User Stories...")

        assigned_stories = []

        for story_id in story_ids:
            story = self._request(
                "GET",
                f"userstories/{story_id}",
            )

            if user_id in story["assigned_users"]:
                assigned_stories.append(
                    {
                        "id": story["id"],
                        "ref": story["ref"],
                        "subject": story["subject"],
                        "description": story["description"],
                    }
                )

        return assigned_stories

    def get_my_sprint_stories(
        self,
        sprint_number,
        sprint_year,
        username,
        password,
    ):
        """
        Retrieve the authenticated user's assigned User Stories for a
        specific sprint.

        This method executes the complete workflow:

        - Authenticate the user.
        - Retrieve the authenticated user's information.
        - Retrieve the user's projects.
        - Locate the requested sprint.
        - Retrieve the sprint User Stories.
        - Filter the stories assigned to the authenticated user.

        Args:
            sprint_number (int):
                Sprint number.

            sprint_year (int):
                Sprint year.

            username (str):
                Taiga username or email.

            password (str):
                Taiga password.

        Returns:
            list[dict]:
                Assigned User Stories. Each dictionary contains the
                story ID, reference number, subject and description.

        Raises:
            Exception:
                If authentication or any API request fails.
        """

        self._get_auth_token(username, password)

        user_id = self.get_current_user()["id"]

        project_ids = self.get_user_projects(user_id)

        story_ids = self.get_sprint_user_story_ids(
            project_ids,
            sprint_number,
            sprint_year,
        )

        return self.get_assigned_user_stories(
            story_ids,
            user_id,
        )
