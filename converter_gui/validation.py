"""Basic output checks; these cannot determine semantic fidelity."""
from pathlib import Path


def validate_markdown(path: Path, content: str) -> list[str]:
    issues = []
    if not path.is_file():
        issues.append("Output file was not created.")
    if not content.strip():
        issues.append("Markdown output is empty.")
    if content.count("```") % 2:
        issues.append("Possible unmatched triple-backtick code fence.")
    if content.count("~~~") % 2:
        issues.append("Possible unmatched tilde code fence.")
    return issues
