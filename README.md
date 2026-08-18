# Dmitry Nesmachny — Architecture Portfolio

Source repository for the personal architecture portfolio published at https://nesmachnydn.github.io/.

The site is generated from `portfolio.json` by `scripts/build_site.py` and deployed through GitHub Actions. Pull requests run regression tests plus generated-site validation; merges to `main` publish the `_site` artifact to GitHub Pages.

## Local validation

```bash
python -m unittest discover -s tests -p 'test_*.py'
python scripts/build_site.py
python scripts/validate_site.py
```

Generated `_site/` content is intentionally not committed.
