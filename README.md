# Universal MarkItDown Converter

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Windows desktop application for batch converting local files to Markdown with [Microsoft MarkItDown](https://github.com/microsoft/markitdown).

## Features

- Convert multiple local files in one batch, with drag and drop.
- Choose an output folder and open it from the application.
- Run conversions in a background Qt thread with overall progress and per-file status.
- Save raw MarkItDown output or opt into conservative cleanup.
- Extract validated embedded images into per-document asset folders and link them with relative paths.
- View conversion logs, errors, and basic Markdown validation notes.
- Avoid overwriting existing output files by assigning a numbered filename when needed.

This tool aims to retain useful content and structure. Conversion quality depends on the input, MarkItDown converter, and optional dependencies; output is not guaranteed to be lossless.

## Supported formats and limits

The application delegates format recognition and conversion to MarkItDown 0.1.8. The supplied dependencies include its DOCX, PDF, PPTX, XLS, and XLSX extras. Common local inputs include:

- Word: DOCX
- PDF
- PowerPoint: PPTX
- Excel: XLSX and legacy XLS (requires MarkItDown's optional spreadsheet dependencies)
- HTML, CSV, EPUB, and plain text
- JSON and many XML documents through MarkItDown's text or RSS routes; structured fidelity varies by input
- Common image formats supported by MarkItDown and Pillow

MarkItDown may recognize additional inputs, but this project does not claim complete coverage for every format or variant. A successful conversion does not guarantee that every heading, table, formula, annotation, image, or other structure was retained. Some image conversions may produce no descriptive Markdown. When image extraction is enabled, the GUI can preserve a supported source image as an asset without inventing OCR or caption text.

Audio transcription is not included in the default setup. MarkItDown's optional audio route can call Google Speech Recognition and may require external network access; it is not guaranteed to be private or offline. Video input does not provide visual scene understanding.

## Requirements

- Windows 10 or later
- 64-bit Python 3.12 or later
- Git
- Internet access for the initial Python package installation

The dependency files install PySide6, MarkItDown 0.1.8 with document and spreadsheet extras, Pillow, and (for development) pytest. Additional MarkItDown integrations may need separate dependencies or services.

## Quick Start (Windows PowerShell)

Copy and run these commands in PowerShell. They clone the public repository, create an isolated environment, install dependencies, and launch the GUI:

```powershell
git clone https://github.com/bootbeat/universal-markitdown-converter.git
Set-Location universal-markitdown-converter
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

The execution-policy command applies only to the current PowerShell process. If script activation is already permitted, you can omit it. If Python's `py` launcher is unavailable, install 64-bit Python 3.12+ and use `python -m venv .venv` instead.

The launcher also checks for `.venv\Scripts\python.exe` in the project directory and relaunches through it when available. Keeping the virtual environment inside the checkout makes the setup portable between machines; `.venv` is ignored by Git.

## Basic use

1. Add files with **Add Files** or drag them into the file list.
2. Choose an output folder.
3. Choose raw Markdown, cleaned Markdown, and/or image extraction.
4. Select **Convert All** and review per-file status, logs, and validation details.
5. Use **Open Output Folder** to review the Markdown and assets.

Existing filenames are preserved where possible; if an output name already exists, the converter appends a number rather than overwriting it.

### Raw Markdown and cleaned Markdown

- **Raw Markdown** is MarkItDown's output without post-processing. It is the best diagnostic comparison with the installed converter.
- **Clean Markdown** applies limited normalization and conservative DOCX structure handling. When cleanup runs, the original MarkItDown text is also saved as a `.raw.md` sidecar.
- **Extract Images** can be enabled independently. Validated assets are saved in a sibling `<document>_assets` folder, and resolvable Markdown references use relative paths. If MarkItDown truncates or omits image data, the converter only replaces references it can safely pair with actual source image bytes.

Raw output is not overwritten by cleanup. Image files are validated before the cleaned Markdown links to them.

## Conversion pipeline

```text
Selected local file
        v
MarkItDown 0.1.8 in the active project Python environment
        v
Raw Markdown (UTF-8)
        v optional
DOCX-aware cleanup and validated asset extraction
        v
Markdown plus relative links to emitted assets
        v
Basic output validation and GUI status
```

The application checks that output exists, is nonempty, and has balanced common code-fence markers. These checks do not establish semantic or structural fidelity.

## Project architecture

```text
app.py                     Windows launcher; selects the checkout's .venv
converter_gui/gui.py       PySide6 interface and background QThread worker
converter_gui/core.py      MarkItDown subprocess, file naming, conversion results
converter_gui/postprocess.py  Markdown cleanup and source-correlated assets
converter_gui/validation.py Basic output checks
tests/                     Unit tests
```

The GUI and conversion core are separate. The core calls MarkItDown in a subprocess using the active Python interpreter and explicitly communicates text as UTF-8.

## Testing

Install the development dependencies after completing the Quick Start setup:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The automated tests cover output naming, basic cleanup, inline image extraction, and output validation. They are not a full-format conversion benchmark.

## Troubleshooting

- **The wrong Python environment is running:** activate `.venv` and check `python -c "import sys; print(sys.executable)"`. The launcher prefers the checkout's `.venv` when it exists.
- **MarkItDown reports that a converter dependency is missing:** verify the environment is active, then run `python -m pip install -r requirements.txt` again. Some less common converters need additional optional integrations.
- **A format converts to little or no Markdown:** check the relevant MarkItDown limitation and optional dependencies. A successful process exit does not guarantee useful content was extracted.
- **An image is not linked:** extraction requires a complete source image that can be paired safely and validated. Unsupported or ambiguous image data is left unlinked rather than replaced with a broken link.
- **PowerShell blocks activation:** use the process-scoped workaround shown in Quick Start, or launch directly with `.\.venv\Scripts\python.exe app.py`.
- **The GUI cannot start:** confirm 64-bit Python 3.12+, reinstall requirements in the active environment, then retry `python app.py`.

## Security and privacy

- The GUI selects local files and writes Markdown/assets to the output folder you choose. It does not upload documents by itself.
- MarkItDown converters can have different network behavior. The optional audio transcription route may send audio to Google Speech Recognition; do not use it for sensitive recordings unless you have reviewed and accepted that service's terms and privacy behavior.
- Only convert documents you trust. Document parsers process complex, potentially malformed input.
- Markdown output and extracted assets may contain the source document's sensitive content. Store and share the output accordingly.
- Do not commit source documents, generated outputs, `.env` files, credentials, or local virtual environments. `.gitignore` excludes common examples of these files.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for the short contributor workflow. Install `requirements-dev.txt`, run the tests, and keep changes focused. Do not edit the installed MarkItDown package to change converter behavior; report converter limitations or implement carefully scoped changes in this project's core/post-processing layer.

### Windows executable packaging

This repository does not currently provide a packaged executable or packaging configuration. The app delegates conversion to a separate Python interpreter, so freezing it needs a deliberate worker/runtime design and format-specific dependency checks. Run from the project virtual environment for now; do not assume a standalone executable is available.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

## Acknowledgements

- [Microsoft MarkItDown](https://github.com/microsoft/markitdown) provides the underlying file-to-Markdown converters.
- [Qt for Python (PySide6)](https://doc.qt.io/qtforpython-6/) provides the desktop GUI framework.
- [Pillow](https://python-pillow.org/) is used to validate image assets.
