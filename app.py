"""Launch the converter with this checkout's virtual environment when available."""
from pathlib import Path
import subprocess
import sys

PROJECT_PYTHON = Path(__file__).resolve().parent / ".venv" / "Scripts" / "python.exe"

if PROJECT_PYTHON.is_file() and Path(sys.executable).resolve() != PROJECT_PYTHON.resolve():
    raise SystemExit(subprocess.call([str(PROJECT_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]],
                                     cwd=str(Path(__file__).resolve().parent)))

from converter_gui.gui import main

if __name__ == "__main__":
    main()

