#!/usr/bin/env python3
"""Split each PDF in an input directory into one PDF per page."""

import argparse
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
    args = parser.parse_args()

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
            total_pages += split_pdf(pdf, args.output_dir)
        except Exception as exc:  # pypdf can raise various errors on bad PDFs
            print(f"::error file={pdf}::Failed to split {pdf.name}: {exc}")
            return 1

    print(f"\nDone. Split {len(pdfs)} PDF(s) into {total_pages} page file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
