# PDF Splitter

A small repository with a GitHub Action that splits every PDF in `input/` into one PDF per page.

## How it works

1. Drop one or more `.pdf` files into the `input/` folder.
2. Commit and push to the default branch.
3. The **Split PDFs** workflow runs automatically. It:
   - Installs Python and `pypdf`.
   - Runs `scripts/split_pdf.py`, which writes each page of `input/foo.pdf` to `output/foo/foo_page_01.pdf`, `foo_page_02.pdf`, ...
   - Uploads the `output/` folder as a workflow artifact called **split-pages** (kept for 30 days).
   - Commits the `output/` folder back to the repo (on push events only).

You can also trigger the workflow manually from the **Actions** tab via *Run workflow*.

## Repository layout

```
.
├── .github/workflows/split-pdfs.yml   # the GitHub Action
├── scripts/split_pdf.py               # splitter script (pypdf)
├── input/                             # put PDFs here
├── output/                            # generated, one folder per source PDF
├── requirements.txt
└── README.md
```

## Run it locally

```bash
pip install -r requirements.txt
python scripts/split_pdf.py --input-dir input --output-dir output
```

Both flags are optional and default to `input` and `output`.

## Creating the GitHub repo

From the unzipped folder:

```bash
git init -b main
git add .
git commit -m "Initial commit: PDF splitter with GitHub Action"
gh repo create pdf-splitter --public --source=. --push
```

(Or create the repo in the GitHub UI and `git remote add origin ... && git push -u origin main`.)

## Permissions note

The workflow needs `contents: write` to commit the split pages back. That's already set in the workflow file. If you'd rather not commit `output/` to the repo, remove the **Commit split pages back to the repo** step — the workflow artifact will still be available for download.
