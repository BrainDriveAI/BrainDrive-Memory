# Contributing to BrainDrive Memory

Thank you for your interest in contributing to BrainDrive Memory AI Agent! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Guidelines](#coding-guidelines)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)
- [Adding New Features](#adding-new-features)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to maintain a respectful, inclusive, and collaborative environment. Please be kind to other contributors, users, and community members.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/memory-ai-agent.git`
3. Set the upstream remote: `git remote add upstream https://github.com/originalowner/memory-ai-agent.git`
4. Create a new branch for your work: `git checkout -b feature/your-feature-name`
5. Set up the development environment (see [Installation Guide](installation.md))

## Development Workflow

1. Keep your fork updated:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. Make your changes in small, logical commits with clear messages

3. Test your changes locally

4. Push to your fork: `git push origin feature/your-feature-name`

5. Create a pull request against the main repository

## Coding Guidelines

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use type hints for function parameters and return values
- Document functions and classes with docstrings
- Maximum line length of 100 characters

### Code Organization

- Keep modules focused on a single responsibility
- Use the established project structure for new code
- Create appropriate interfaces for new data source providers
- Use dependency injection where appropriate

### Naming Conventions

- Use `snake_case` for variables and functions
- Use `PascalCase` for classes
- Use `UPPER_CASE` for constants
- Use descriptive names that reflect purpose

## Pull Request Process

1. Ensure your code follows the project's style guidelines
2. Update the documentation if necessary
3. Reference any relevant issues in your PR description
4. Wait for review from maintainers
5. Address any feedback or requested changes
6. Once approved, your PR will be merged

## Project Structure

The repository follows this structure:

```
braindrive-memory/
├── app/                  # Main application code
│   ├── adapters/         # Adapters for external services
│   ├── agents/           # Agent implementation
│   ├── agent_prompts/    # Prompts for agent behavior
│   ├── interfaces/       # Interface definitions for data sources
│   ├── presentation/     # UI and API components
│   ├── services/         # Application services
│   ├── tools/            # Agent tools
│   └── utils/            # Utility functions
├── docs/                 # Documentation
└── main.py               # Application entry point
```

### Key Components

- **Interfaces**: Define abstract interfaces for services (e.g., `GraphDBInterface`)
- **Adapters**: Implement interfaces for specific providers (e.g., `Neo4jAdapter`)
- **Tools**: Agent tools for interacting with stored knowledge
- **Agents**: Implementation of the agent's reasoning system
- **Presentation**: User interfaces (Streamlit, API)

## Adding New Features

### New Data Source Providers

To add support for a new data source provider (e.g., a new vector store):

1. Create an adapter in the appropriate adapter directory
2. Implement the corresponding interface
3. Update the data source manager to recognize your provider
4. Update documentation
5. Add any required environment variables

### New Agent Tools

To add a new tool for the agent:

1. Create a new file in the appropriate tools directory
2. Implement the tool following the LangChain tool pattern
3. Add the tool to the tools list in `react_graph_agent.py`
4. Update the agent prompts if necessary


## Documentation

- Update README and related documentation for significant changes
- Document new features in appropriate guides
- Include examples for new functionality

## Environment Variables and Security

- Never commit API keys or secrets
- Add new environment variables to:
  - `.env.example`
  - Documentation in the configuration guide
  - The `AppSettings` class in `app_env.py`

## Need Help?

If you need assistance with your contribution:

- Open an issue with questions
- Ask in the project's community channels
- Contact the maintainers

Thank you for contributing to BrainDrive Memory!
