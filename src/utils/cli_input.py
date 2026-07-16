"""
Utility functions for reading and validating user input from the command
line.

This module provides reusable helpers for prompting users for common
input types such as passwords, integers, and non-empty strings.
"""

from getpass import getpass


def read_password(prompt: str) -> str:
    """
    Prompt the user for a password without echoing the entered
    characters.

    Args:
        prompt (str):
            Message displayed to the user before reading the password.

    Returns:
        str:
            The password entered by the user.
    """

    return getpass(prompt)


def read_int(prompt: str, error_message: str) -> int:
    """
    Prompt the user until a valid integer is entered.

    Args:
        prompt (str):
            Message displayed to the user.

        error_message (str):
            Message displayed when the input cannot be converted to an
            integer.

    Returns:
        int:
            The integer entered by the user.
    """

    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print(error_message)


def read_str(prompt: str, error_message: str) -> str:
    """
    Prompt the user until a non-empty string is entered.

    Leading and trailing whitespace is removed before validating the
    input.

    Args:
        prompt (str):
            Message displayed to the user.

        error_message (str):
            Message displayed when the input is empty.

    Returns:
        str:
            The trimmed string entered by the user.
    """

    while True:
        value = input(prompt).strip()

        if value:
            return value

        print(error_message)
