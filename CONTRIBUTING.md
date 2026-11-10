# Contributing to DevAid

Thank you for your interest in contributing!

## Development principles

- Keep changes modular and maintainable.
- Write tests for new functionality.
- Document public interfaces.
- Respect user privacy.
- Avoid mandatory paid services.

## Workflow

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your changes.
4. Submit a pull request.

## Documentation checks

Run the local Markdown link checker before submitting documentation changes:

```bash
uv run python scripts/check_markdown_links.py
```

The checker validates relative file links and Markdown heading anchors without making network requests. External URLs are intentionally not fetched, so CI does not depend on third-party website availability.
