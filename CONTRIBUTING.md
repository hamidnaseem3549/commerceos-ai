# Contributing to CommerceOS AI

## Development Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/commerceos-ai.git
   cd commerceos-ai
   ```

2. **Set up environment**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   # source venv/bin/activate    # macOS/Linux
   pip install -r requirements.txt
   cp .env.example .env
   # Add your GROQ_API_KEY and ADMIN_PASSWORD to .env
   ```

3. **Initialize database**
   ```bash
   python scripts/seed.py
   python rag/vectorstore_setup.py
   ```

## Code Standards

- **Python:** Follow PEP 8
- **Linting:** Run `ruff check .` before committing
- **Docstrings:** Google-style for all public modules and functions
- **Testing:** All PRs must include tests for new functionality

## Commit Conventions

We use conventional commits:

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `ci:` — CI/CD changes
- `refactor:` — Code restructuring
- `test:` — Test additions
- `chore:` — Tooling, dependencies

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear commit messages
3. Run `ruff check .` and `pytest tests/ -v` — both must pass
4. Open a PR with a descriptive title and summary
5. Wait for CI to pass before merging

## Adding a New Agent

1. Create `commerceos/agents/your_agent.py` (subclass `BaseAgent`)
2. Add to `commerceos/agents/__init__.py` (register + import)
3. Add to supervisor routing in `commerceos/orchestration/supervisor.py`
4. Write tests in `tests/`
5. Done — no hardcoded routing required
