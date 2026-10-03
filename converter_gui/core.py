"""Conversion core backed by the explicitly configured MarkItDown environment."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Callable, Iterable
import importlib.metadata

from .postprocess import cleanup_document
from .validation import validate_markdown

DEFAULT_PYTHON = Path(sys.executable).resolve()

@dataclass(frozen=True)
class ConversionResult:
    source: Path
    output: Path | None
    success: bool
    message: str

def resolve_python(python: Path = DEFAULT_PYTHON) -> Path:
    resolved = python.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Configured MarkItDown Python was not found: {resolved}")
    return resolved

def invoke_markitdown(source: Path, python: Path = DEFAULT_PYTHON) -> str:
    """Return unmodified Markdown from MarkItDown."""
    executable = resolve_python(python)
    source = source.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Input file was not found: {source}")
    script = ("import sys, importlib.metadata; "
              "sys.stdout.reconfigure(encoding='utf-8', errors='strict'); "
              "sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace'); "
              "version = importlib.metadata.version('markitdown'); "
              "assert version == '0.1.8', f'Expected MarkItDown 0.1.8, found {version}'; "
              "from markitdown import MarkItDown; "
              "result = MarkItDown().convert(sys.argv[1]); "
              "sys.stdout.write(str(result.markdown or str()))")
    completed = subprocess.run([str(executable), "-X", "utf8", "-c", script, str(source)],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="strict", check=False)
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or f"MarkItDown exited with status {completed.returncode}")
    return completed.stdout

def reserve_output_path(source: Path, output_dir: Path) -> Path:
    """Atomically reserve a fresh Markdown filename."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = source.stem or "converted"
    index = 0
    while True:
        suffix = "" if index == 0 else f" ({index})"
        candidate = output_dir / f"{stem}{suffix}.md"
        try:
            with candidate.open("x", encoding="utf-8"):
                pass
            return candidate
        except FileExistsError:
            index += 1

def convert_one(source: Path, output_dir: Path, python: Path = DEFAULT_PYTHON,
                cleanup: bool = False, manage_images: bool = False) -> ConversionResult:
    source = Path(source)
    target = None
    try:
        markdown = invoke_markitdown(source, python)
        target = reserve_output_path(source, Path(output_dir))
        final_markdown = markdown
        assets = []
        postprocess_warnings = []
        if cleanup or manage_images:
            processed = cleanup_document(markdown, target, manage_images, source)
            final_markdown, assets = processed.markdown, processed.assets
            postprocess_warnings = processed.warnings
            raw_target = target.with_name(target.stem + ".raw.md")
            index = 1
            while raw_target.exists():
                raw_target = target.with_name(f"{target.stem}.raw ({index}).md")
                index += 1
            with raw_target.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(markdown)
        target.write_text(final_markdown, encoding="utf-8", newline="\n")
        issues = validate_markdown(target, final_markdown)
        details = "Converted raw MarkItDown output."
        if cleanup or manage_images:
            details = f"Converted with optional cleanup; raw output: {raw_target.name}."
        if assets:
            details += f" Extracted {len(assets)} image asset(s)."
        if postprocess_warnings:
            details += " Post-processing: " + " ".join(postprocess_warnings)
        if issues:
            details += " Validation: " + " ".join(issues)
        return ConversionResult(source, target, True, details)
    except Exception as exc:
        if target is not None:
            try:
                target.unlink()
            except OSError:
                pass
        return ConversionResult(source, target, False, str(exc))

def convert_many(sources: Iterable[Path], output_dir: Path, python: Path = DEFAULT_PYTHON,
                 on_result: Callable[[ConversionResult], None] | None = None,
                 cleanup: bool = False, manage_images: bool = False) -> list[ConversionResult]:
    results = []
    for source in sources:
        result = convert_one(Path(source), output_dir, python, cleanup, manage_images)
        results.append(result)
        if on_result:
            on_result(result)
    return results


