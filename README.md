# Dmitry Nesmachny — Architecture Portfolio

Source repository for the personal architecture portfolio published at https://nesmachnydn.github.io/.

The root page is Russian by default and is intended as the primary permanent-employment portfolio. The English version is published at https://nesmachnydn.github.io/en/ and both versions provide an RU/EN switcher.

The site is generated from `portfolio.json` by `scripts/build_site.py` and deployed through GitHub Actions. The Pages workflow runs only for `main` (or explicit manual dispatch): it executes regression tests, builds both localized pages, validates the generated site and publishes the `_site` artifact.

## Local validation

```bash
python -m unittest discover -s tests -p 'test_*.py'
python scripts/build_site.py
python scripts/validate_site.py
```

Generated `_site/` content is intentionally not committed.
