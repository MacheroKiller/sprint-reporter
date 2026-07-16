"""
Client for generating sprint report paragraphs using a language model.

This module prepares User Story descriptions, removes acceptance
criteria, truncates excessively long content, and sends the cleaned
stories to an AI service to generate formal progress report paragraphs
in Spanish.
"""

import json
import os
import re

import requests


# Headings that indicate the beginning of the acceptance criteria
# section. Everything after one of these markers is discarded before
# sending the description to the language model.
ACCEPTANCE_CRITERIA_MARKERS = [
    r"criterios? de aceptaci[oó]n / escenarios?",
    r"acceptance criteria",
]

_marker_pattern = re.compile(
    "(" + "|".join(ACCEPTANCE_CRITERIA_MARKERS) + ")",
    re.IGNORECASE,
)

# Maximum number of characters from the description that will be sent
# to the language model.
MAX_DESCRIPTION_CHARS = 2500


def clean_description(description: str) -> str:
    """
    Remove acceptance criteria and truncate long descriptions.

    The function searches for the first occurrence of any configured
    acceptance criteria marker. If found, everything after that marker
    is discarded. The resulting description is then trimmed and limited
    to ``MAX_DESCRIPTION_CHARS`` characters, attempting to preserve the
    last complete sentence.

    Args:
        description (str):
            Original User Story description.

    Returns:
        str:
            Cleaned description suitable for sending to the AI service.
    """

    match = _marker_pattern.search(description)

    trimmed = description[: match.start()] if match else description
    trimmed = trimmed.strip()

    if len(trimmed) > MAX_DESCRIPTION_CHARS:
        trimmed = trimmed[:MAX_DESCRIPTION_CHARS].rsplit(".", 1)[0] + "."

    return trimmed


class IaConnection:
    """
    Client for interacting with the AI report generation service.

    The service receives cleaned User Stories and returns a formal
    paragraph describing the implemented functionality for inclusion in
    sprint progress reports.
    """

    def making_report(self, stories):
        """
        Generate a report paragraph for each User Story.

        Each story is cleaned before being sent to the AI service. The
        generated paragraphs are returned as a single string separated by
        blank lines.

        Args:
            stories (list[dict]):
                Collection of User Stories. Each story is expected to
                contain at least the following fields:

                - ``ref``
                - ``subject``
                - ``description``

        Returns:
            str:
                Generated report containing one paragraph per User Story.

        Raises:
            requests.RequestException:
                If the request to the AI service fails.

            KeyError:
                If the AI response does not contain the expected fields.
        """

        paragraphs = []

        for story in stories:
            clean_story = {
                **story,
                "description": clean_description(story["description"]),
            }

            response = requests.post(
                os.getenv("IA_URL"),
                json={
                    "model": "qwen3:8b",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Analiza la siguiente user story y genera "
                                "un único párrafo formal en español para "
                                "un reporte de avance. Debe empezar "
                                "exactamente con: "
                                "'Durante el periodo reportado, se realizó "
                                "la historia <ref>: <título>, donde...' "
                                "Usa el campo ref como número y subject "
                                "como título (elimina prefijos como 'EQ4:' "
                                "cuando no aporten valor). Sintetiza la "
                                "funcionalidad implementada basándote SOLO "
                                "en la descripción proporcionada. No "
                                "inventes información que no esté "
                                "explícitamente en el texto. IMPORTANTE: "
                                "tu única salida permitida es un párrafo "
                                "de texto plano. Está prohibido usar "
                                "encabezados (#), listas, numeraciones o "
                                "cualquier estructura distinta a prosa "
                                "corrida, sin importar cómo esté organizada "
                                "la información de entrada. Devuelve solo "
                                "el párrafo final, sin Markdown ni "
                                "explicaciones."
                            ),
                        },
                        {
                            "role": "user",
                            "content": json.dumps(
                                clean_story,
                                ensure_ascii=False,
                                indent=2,
                            ),
                        },
                    ],
                    "options": {
                        "num_ctx": 8192,
                    },
                    "stream": False,
                },
            )

            response.raise_for_status()

            paragraphs.append(response.json()["message"]["content"])

        return "\n\n".join(paragraphs)
