import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


def sanitize_filename_component(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", value or "model")
    sanitized = sanitized.strip("._-")
    return sanitized or "model"


def build_export_path(output_dir: Union[str, Path], document_name: str, timestamp: Optional[str] = None) -> Path:
    export_dir = Path(output_dir).expanduser()
    export_dir.mkdir(parents=True, exist_ok=True)

    stamp = timestamp or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_name = sanitize_filename_component(document_name)
    return export_dir / f"{base_name}_{stamp}.stl"


def resolve_bambu_studio_executable(explicit_path: Optional[str] = None) -> Optional[str]:
    candidates = []

    if explicit_path:
        candidates.append(explicit_path)

    env_path = os.getenv("BAMBU_STUDIO_PATH")
    if env_path:
        candidates.append(env_path)

    candidates.extend(
        [
            r"C:\Program Files\Bambu Studio\Bambu Studio.exe",
            r"C:\Program Files\Bambu Studio\BambuStudio.exe",
            r"C:\Program Files (x86)\Bambu Studio\Bambu Studio.exe",
            r"C:\Program Files (x86)\Bambu Studio\BambuStudio.exe",
        ]
    )

    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path.is_file():
            return str(path)

    for command in ("Bambu Studio", "BambuStudio", "bambu-studio"):
        resolved = shutil.which(command)
        if resolved:
            return resolved

    return None
