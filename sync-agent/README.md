# Sync-Agent

Autonomous repository lifecycle manager.

## Architecture

- **Core Agents**: Deterministic logic for Git operations and file management.
- **AI Agents**: Gemini-powered reasoning for diff analysis and natural language interaction.
- **Audit System**: Structured logging of every lifecycle event.

## Usage

1. Provide local path and remote URL.
2. The **Input Agent** validates connectivity.
3. The **Sync Agent** calculates divergences.
4. The **Analysis Agent** summarizes changes.
5. The **Update Agent** commits sync notes.
6. The **Cleanup Agent** removes local artifacts after explicit confirmation.
