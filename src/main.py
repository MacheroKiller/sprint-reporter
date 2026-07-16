"""
Application entry point.

Prompts the user for sprint information and Taiga credentials, retrieves
the user stories assigned to the authenticated user for the selected
sprint, and generates a sprint summary using the AI reporting service.
"""

from taiga_client import TaigaClient
from ia_connection import IaConnection
from utils.cli_input import read_int, read_str, read_password


def main():
    """
    Execute the sprint reporting workflow.

    The workflow performs the following steps:

    - Read the sprint number and year.
    - Read the user's Taiga credentials.
    - Authenticate against Taiga.
    - Retrieve the user stories assigned to the authenticated user
      within the specified sprint.
    - Generate an AI-based sprint summary if user stories are found.

    Returns:
        None
    """
    client = TaigaClient()

    sprint_number = read_int("# of sprint: ", "Sprint number must be a number.")
    sprint_year = read_int("Year of sprint: ", "Sprint year must be a number.")
    user_email = read_str("Username / Email: ", "Invalid argument.")
    user_password = read_password("Password: ")

    try:
        user_stories = client.get_my_sprint_stories(
            sprint_number,
            sprint_year,
            user_email,
            user_password,
        )
    except Exception as e:
        print(f"Could not retrieve the information: {e}")
        return

    print(f"Assigned User Stories: {user_stories}")

    if not user_stories:
        print("No user stories were found for the selected sprint.")
        return

    print("Generating report...")

    ia_report = IaConnection()
    sprint_report = ia_report.making_report(user_stories)

    print(f"Report:\n{sprint_report}")


if __name__ == "__main__":
    main()
