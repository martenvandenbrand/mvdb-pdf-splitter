#!/usr/bin/env python3
"""Split each PDF in an input directory into one PDF per page."""

import argparse
import json
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def split_pdf(pdf_path: Path, output_dir: Path) -> int:
    """Split a single PDF into one file per page. Returns number of pages written."""
    reader = PdfReader(str(pdf_path))
    stem = pdf_path.stem
    num_pages = len(reader.pages)
    # Zero-pad page numbers so files sort naturally
    pad = max(2, len(str(num_pages)))

    target_dir = output_dir / stem
    target_dir.mkdir(parents=True, exist_ok=True)

    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        out_path = target_dir / f"{stem}_page_{i:0{pad}d}.pdf"
        with open(out_path, "wb") as f:
            writer.write(f)
        print(f"  wrote {out_path.relative_to(output_dir.parent)}")

    return num_pages


def parse_ranges(spec: str, num_pages: int) -> list[tuple[int, int]]:
    """Parse a spec like '1-7,8-10,11-27' into 0-based [start, end) page ranges."""
    ranges = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start, end = int(start_s), int(end_s)
        else:
            start = end = int(part)
        if start < 1 or end < start or end > num_pages:
            raise ValueError(f"Invalid range '{part}' for a {num_pages}-page PDF")
        ranges.append((start - 1, end))
    return ranges


def split_pdf_by_ranges(pdf_path: Path, output_dir: Path, ranges: list[tuple[int, int]]) -> int:
    """Split a single PDF into the given page ranges. Returns number of parts written."""
    reader = PdfReader(str(pdf_path))
    stem = pdf_path.stem
    num_pages = len(reader.pages)
    pad = max(2, len(str(len(ranges))))

    target_dir = output_dir / stem
    target_dir.mkdir(parents=True, exist_ok=True)

    for i, (start, end) in enumerate(ranges, start=1):
        if end > num_pages:
            raise ValueError(f"Range {start + 1}-{end} exceeds {num_pages} pages in {pdf_path.name}")
        writer = PdfWriter()
        for page in reader.pages[start:end]:
            writer.add_page(page)
        out_path = target_dir / f"{stem}_part_{i:0{pad}d}_p{start + 1}-{end}.pdf"
        with open(out_path, "wb") as f:
            writer.write(f)
        print(f"  wrote {out_path.relative_to(output_dir.parent)}")

    return len(ranges)


def load_split_config(config_path: Path) -> dict[str, str]:
    """Load a JSON config mapping PDF filenames (or '*' for a default) to range specs.

    Example:
        {
            "*": "1-5,6-10",
            "report-2026.pdf": "1-7,8-10,11-27"
        }
    """
    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Config {config_path} must be a JSON object mapping filenames to range specs")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Split PDFs into one file per page.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("input"),
        help="Directory containing PDF files to split (default: input)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory to write the split pages into (default: output)",
    )
    parser.add_argument(
        "--ranges",
        type=str,
        default=None,
        help=(
            "Comma-separated page ranges to split into instead of one-per-page, "
            "e.g. '1-7,8-10,11-27' (1-based, inclusive). Applies to every PDF."
        ),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=(
            "Path to a JSON file mapping PDF filenames to range specs, with an "
            "optional '*' key as the default for files not listed (see split-config.json)"
        ),
    )
    args = parser.parse_args()

    config = load_split_config(args.config) if args.config and args.config.is_file() else {}

    if not args.input_dir.is_dir():
        print(f"::error::Input directory not found: {args.input_dir}")
        return 1

    pdfs = sorted(args.input_dir.glob("*.pdf"))
    if not pdfs:
        print(f"::warning::No PDF files found in {args.input_dir}")
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)

    total_pages = 0
    for pdf in pdfs:
        print(f"Splitting {pdf.name}...")
        try:
            spec = args.ranges or config.get(pdf.name) or config.get("*")
            if spec:
                reader = PdfReader(str(pdf))
                ranges = parse_ranges(spec, len(reader.pages))
                total_pages += split_pdf_by_ranges(pdf, args.output_dir, ranges)
            else:
                total_pages += split_pdf(pdf, args.output_dir)
        except Exception as exc:  # pypdf can raise various errors on bad PDFs
            print(f"::error file={pdf}::Failed to split {pdf.name}: {exc}")
            return 1

    print(f"\nDone. Split {len(pdfs)} PDF(s) into {total_pages} page file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
