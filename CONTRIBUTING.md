# Contributing to Document Processing Platform

Thank you for your interest in contributing to the Document Processing Platform! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Issue Guidelines](#issue-guidelines)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Release Process](#release-process)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](.github/CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker and Docker Compose
- Git

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/document-processing-platform.git
   cd document-processing-platform
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/original-owner/document-processing-platform.git
   ```

## Development Setup

### Backend Setup

1. Create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the development server:
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

### Docker Setup

For a complete environment with all services:

```bash
docker-compose up -d
```

## Project Structure

```
document-processing-platform/
├── backend/                 # FastAPI backend
│   ├── api/                # API routes and main app
│   ├── core/               # Core configuration and utilities
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic services
│   └── tests/              # Backend tests
├── frontend/               # React frontend
│   ├── public/             # Static files
│   ├── src/                # React source code
│   └── tests/              # Frontend tests
├── docs/                   # Documentation
├── .github/                # GitHub configurations
└── docker-compose.yml      # Docker orchestration
```

## Coding Standards

### Python (Backend)

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Use meaningful variable and function names
- Keep functions small and focused

Example:
```python
from typing import Optional, List
from pydantic import BaseModel

def process_document(
    document_id: int,
    user_id: Optional[int] = None
) -> List[dict]:
    """
    Process a document with OCR and NLP analysis.
    
    Args:
        document_id: The ID of the document to process
        user_id: Optional user ID for audit logging
        
    Returns:
        List of processing results
        
    Raises:
        DocumentNotFoundError: If document doesn't exist
    """
    # Implementation here
    pass
```

### TypeScript/JavaScript (Frontend)

- Use TypeScript for all new code
- Follow ESLint and Prettier configurations
- Use functional components with hooks
- Implement proper error handling
- Use meaningful component and variable names

Example:
```typescript
import React, { useState, useEffect } from 'react';
import { Document } from '../types';

interface DocumentListProps {
  documents: Document[];
  onDocumentSelect: (document: Document) => void;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  onDocumentSelect
}) => {
  const [filteredDocs, setFilteredDocs] = useState<Document[]>([]);

  useEffect(() => {
    setFilteredDocs(documents);
  }, [documents]);

  return (
    <div className="document-list">
      {filteredDocs.map((doc) => (
        <DocumentItem
          key={doc.id}
          document={doc}
          onClick={() => onDocumentSelect(doc)}
        />
      ))}
    </div>
  );
};
```

## Testing

### Backend Testing

1. Run all tests:
   ```bash
   cd backend
   pytest
   ```

2. Run with coverage:
   ```bash
   pytest --cov=. --cov-report=html
   ```

3. Run specific test files:
   ```bash
   pytest tests/test_auth.py
   ```

### Frontend Testing

1. Run all tests:
   ```bash
   cd frontend
   npm test
   ```

2. Run with coverage:
   ```bash
   npm test -- --coverage
   ```

### Writing Tests

- Write tests for all new functionality
- Aim for at least 80% code coverage
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies

Example backend test:
```python
import pytest
from unittest.mock import Mock, patch
from services.auth_service import AuthService

def test_authenticate_user_success():
    """Test successful user authentication."""
    mock_db = Mock()
    mock_user = Mock()
    mock_user.verify_password.return_value = True
    
    with patch('services.auth_service.get_user_by_email', return_value=mock_user):
        result = AuthService.authenticate_user(mock_db, "test@example.com", "password")
        
    assert result == mock_user
    mock_user.verify_password.assert_called_once_with("password")
```

## Submitting Changes

### Workflow

1. Create a feature branch from `develop`:
   ```bash
   git checkout develop
   git pull upstream develop
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "feat: add new document processing feature"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a pull request against the `develop` branch

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add document batch processing
fix: resolve authentication token expiration issue
docs: update API documentation
test: add unit tests for OCR service
```

## Issue Guidelines

### Before Creating an Issue

1. Search existing issues to avoid duplicates
2. Check the documentation for solutions
3. Try to reproduce the issue in a clean environment

### Issue Template

Use the provided issue templates:
- [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md)
- [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md)
- [Documentation](.github/ISSUE_TEMPLATE/documentation.md)

### Good Issue Examples

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Relevant logs or screenshots

## Pull Request Guidelines

### Before Submitting

1. Ensure all tests pass
2. Update documentation if needed
3. Follow coding standards
4. Add tests for new functionality
5. Update changelog if applicable

### PR Template

Use the provided [pull request template](.github/pull_request_template.md) and fill out all relevant sections.

### Review Process

1. Automated checks must pass (CI/CD)
2. At least one maintainer must approve
3. All conversations must be resolved
4. Code must be up to date with target branch

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes (backward compatible)

### Release Steps

1. Create a release branch from `develop`
2. Update version numbers and changelog
3. Run full test suite
4. Create a pull request to `main`
5. After approval, merge and create a release tag
6. Deploy to production

## Getting Help

- Check the [documentation](README.md)
- Search existing [issues](https://github.com/your-username/document-processing-platform/issues)
- Join our [discussions](https://github.com/your-username/document-processing-platform/discussions)
- Contact maintainers via email

## Recognition

Contributors will be recognized in:
- Release notes
- Contributors section in README
- Project documentation

Thank you for contributing to the Document Processing Platform! 🚀
