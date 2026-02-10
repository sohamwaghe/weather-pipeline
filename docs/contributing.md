# Contributing to Weather Data Pipeline

Thank you for your interest in contributing! This guide outlines how to set up your environment and submit changes.

## 🛠️ Local Development Setup

### 1. Prerequisites
- Python 3.11
- Docker & Docker Compose
- [Pre-commit](https://pre-commit.com/)

### 2. Environment Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd weather-pipeline

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

## 🧪 Testing

### Running Linters Locally
We use `black`, `flake8`, `isort`, and `sqlfluff`. You can run them manually or let the pre-commit hooks handle it.
```bash
pre-commit run --all-files
```

### Running dbt Tests
```bash
cd dbt
dbt compile
dbt test
```

## 🚀 Pull Request Process
1. Create a new branch: `git checkout -b feature/your-feature-name`.
2. Commit your changes. Pre-commit hooks will automatically format your code.
3. Ensure the GitHub Actions CI pass for your PR.
4. Request a review from the maintainers.

## 🛡️ Code Style Standards
- **Python**: Follows Black formatting and PEP8.
- **SQL**: Keywords should be lowercase. Indentation is 4 spaces.
- **Git**: Use descriptive commit messages.
