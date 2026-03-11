"""
Shared utility functions used across StegHunter.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

import numpy as np

# ---------------------------------------------------------------------------
# Image file helpers
# ---------------------------------------------------------------------------

SUPPORTED_IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
)


def collect_image_files(
    directory: str | Path, recursive: bool = False
) -> list[Path]:
    """Return all supported image files under *directory*.

    Args:
        directory: Root directory to search.
        recursive: When *True* descend into sub-directories.

    Returns:
        Sorted list of :class:`~pathlib.Path` objects.
    """
    directory = Path(directory)
    glob = directory.rglob("*") if recursive else directory.glob("*")
    return sorted(
        p for p in glob if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    )


# ---------------------------------------------------------------------------
# JSON / NumPy serialisation helpers
# ---------------------------------------------------------------------------

def convert_numpy_types(obj: Any) -> Any:
    """Recursively convert NumPy scalars and arrays to native Python types.

    This makes any result dict safe to pass to :func:`json.dumps`.
    """
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        converted = [convert_numpy_types(item) for item in obj]
        return type(obj)(converted)
    return obj


def save_results_json(results: list[dict], output_path: str | Path) -> None:
    """Serialise *results* to a JSON file at *output_path*."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    converted = [convert_numpy_types(r) for r in results]
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(converted, fh, indent=2, default=str)


def save_results_csv(results: list[dict], output_path: str | Path) -> None:
    """Write heuristic or ML *results* to a CSV file at *output_path*."""
    import csv

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)

        if results and "prediction" in results[0]:
            # ML results
            writer.writerow(
                ["Filename", "File Path", "Method", "Prediction", "Probability", "Confidence", "Status"]
            )
            for r in results:
                pred = "STEGO" if r["prediction"] == 1 else "CLEAN"
                writer.writerow(
                    [
                        r.get("filename", ""),
                        r.get("file_path", r.get("full_path", "")),
                        r.get("method", "ML-based"),
                        pred,
                        f"{r.get('probability', 0):.4f}",
                        f"{r.get('confidence', 0):.4f}",
                        r.get("status", pred),
                    ]
                )
        else:
            # Heuristic results
            writer.writerow(
                [
                    "Filename", "File Size", "Format", "Dimensions", "Mode",
                    "Final Score", "Status", "LSB Score", "Basic Score",
                    "Chi-Square Score", "Pixel Diff Score",
                ]
            )
            for r in results:
                dims = r.get("dimensions", (0, 0))
                score = r.get("final_suspicion_score", 0)
                methods = r.get("methods", {})
                writer.writerow(
                    [
                        r.get("filename", ""),
                        r.get("file_size", ""),
                        r.get("format", ""),
                        f"{dims[0]}x{dims[1]}",
                        r.get("mode", ""),
                        score,
                        "HIGH" if score >= 50 else "LOW",
                        methods.get("lsb", {}).get("lsb_suspicion_score", ""),
                        methods.get("basic", {}).get("basic_suspicion_score", ""),
                        methods.get("chi_square", {}).get("suspicion_score", ""),
                        methods.get("pixel_differencing", {}).get("suspicion_score", ""),
                    ]
                )
