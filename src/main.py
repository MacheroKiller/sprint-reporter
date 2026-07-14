"""
Entry point: fetches the User Stories assigned to the authenticated
user within the configured sprint, using TaigaClient.
"""

from taiga_client import TaigaClient

# Sprint slug prefix used to filter milestones
SPRINT_SLUG = "sprint-07-2026"


def main():
    client = TaigaClient()
    user_stories = client.get_my_sprint_stories(SPRINT_SLUG)

    print(f"Assigned User Stories: {len(user_stories)}")


if __name__ == "__main__":
    main()
