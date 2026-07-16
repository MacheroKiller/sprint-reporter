# sprint-reporter

A small CLI tool that connects to a [Taiga](https://taiga.io/) project management instance, pulls the User Stories assigned to you within a given sprint, and uses a locally-running LLM (via [Ollama](https://ollama.com/)) to generate a plain-language progress report — no cloud API calls, no API costs.

> **Status: hobby project, work in progress.** This was built to solve a personal, recurring need (writing sprint reports by hand from a Taiga instance with inconsistent data). It is **not** intended for production use in its current form — no test suite yet, minimal error handling, and the architecture is still evolving. See [Roadmap](#roadmap) below.

## Why this exists

Manually reading through dozens of Taiga user stories — often full of Markdown, screenshots, and long Gherkin acceptance-criteria blocks — to write a short progress summary is tedious. This tool automates that: it fetches your assigned stories for a sprint, strips out the noise (acceptance criteria, QA scenarios), and asks a local LLM to synthesize each one into a single formal paragraph suitable for a report.

Everything runs locally except the Taiga API calls, so there's no per-request cost and no story content leaves your machine.

## How it works

```
┌─────────────┐      ┌────────────────┐      ┌───────────────┐
│ Taiga API   │ ───▶ │ TaigaClient    │ ───▶ │ IaConnection  │ ───▶ report text
│ (REST)      │      │ (auth, fetch,  │      │ (clean + LLM  │
│             │      │  filter stories)│      │  via Ollama)  │
└─────────────┘      └────────────────┘      └───────────────┘
```

1. **Authenticate** against the Taiga API with your username/password (entered interactively; nothing is persisted to disk).
2. **Resolve** your projects, locate the milestone matching the requested sprint number/year (handles zero-padding differences like `sprint-6-2026` vs `sprint-06-2026`), and fetch the User Stories assigned to you.
3. **Clean** each story's description — acceptance criteria and Gherkin scenarios are trimmed out before it reaches the LLM, since they add noise without adding value to an executive summary.
4. **Summarize** each story individually through a local model (`qwen3:14b` by default) running in Ollama, and concatenate the paragraphs into the final report.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed and running locally, with a model pulled (e.g. `ollama pull qwen3:14b`)
- Access credentials to a Taiga instance

## Installation

```bash
git clone https://github.com/MacheroKiller/sprint-reporter.git
cd sprint-reporter
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
TAIGA_URL=https://your-taiga-instance.example.com/api/v1/
IA_URL=http://localhost:11434/api/chat
```

Credentials (username/password) are **not** stored in `.env` — they're requested interactively each time the script runs, and the password input is hidden.

## Usage

```bash
python src/main.py
```

Example session:

```
# of sprint: 7
Year of sprint: 2026
Username / Email: userTest@email.com
Password:
Retrieving authenticated user information...
Retrieving user projects...
Retrieving sprint User Story IDs...
Retrieving assigned User Stories...
Number of stories assigned to user: 2
Generating report...
Report:
Durante el periodo reportado, se realizó la historia 01: Tutorial interactivo, donde se
implementó un recorrido guiado e interactivo para usuarios al ingresar al panel, utilizando
la librería Driver.js para destacar componentes de la interfaz, mostrar descripciones claras
de su propósito y funcionamiento, y permitir avanzar, retroceder, omitir o finalizar el
recorrido en cualquier momento. La funcionalidad se diseñó para ejecutarse una única vez por
usuario, siguiendo el flujo definido y las especificaciones de diseño, sin interferir con la
navegación normal del panel ni afectar su funcionamiento, garantizando compatibilidad en
dispositivos soportados.

Durante el periodo reportado, se realizó la historia 2: Edición de datos de facturación
electrónica, donde se implementó un formulario para editar la información de facturación
electrónica con campos obligatorios como tipo de persona, tipo de documento, número de
documento, nombres, apellidos, correo electrónico, teléfono, municipio, departamento y
dirección principal, además de campos opcionales como segundo nombre y segundo apellido. Se
incluyó un componente condicional para la carga del RUT, visible solo cuando el tipo de
persona es jurídica, con restricciones de formato .PDF, .JPG, .PNG o .DOC y peso máximo de
10Mb, y se agregó una validación para asegurar que los datos del RUT coincidan con la
información registrada en el formulario antes de permitir la actualización en la base de
datos.
```

(The report is generated in Spanish by default — that's configurable in the system prompt inside `src/ia_connection.py`.)

## Project structure

```
sprint-reporter/
├── src/
│   ├── main.py            # Entry point: CLI prompts + orchestration
│   ├── taiga_client.py    # Taiga API auth, fetching and filtering
│   ├── ia_connection.py   # Description cleanup + local LLM prompting
│   └── utils/
│       └── cli_input.py   # Reusable, validated terminal input helpers
├── requirements.txt
└── README.md
```

## Roadmap

This is an evolving hobby project. Planned next steps:

- [ ] Export the generated report into a template (Word/PDF) instead of printing to the terminal
- [ ] Telegram bot integration to request/receive reports on demand
- [ ] Unit test suite (Taiga client mocked, description-cleaning logic, prompt formatting)
- [ ] Custom exception types instead of generic `Exception`
- [ ] Structured logging instead of `print()`

## Built with

- [Python](https://www.python.org/)
- [Ollama](https://ollama.com/) — local LLM runtime
- [Qwen3](https://ollama.com/library/qwen3) — the default summarization model
- [Taiga API](https://docs.taiga.io/api.html)

## License

MIT — see [LICENSE](LICENSE).