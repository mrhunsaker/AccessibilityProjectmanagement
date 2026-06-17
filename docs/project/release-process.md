# Release Process

APM uses **calendar versioning**: `YYYY.M.N` (year, month, patch).

---

## 🔖 Steps

1. **Update `CHANGELOG.md`** with the new version heading and changes.
2. **Bump the version** in `pyproject.toml` (or wherever `__version__` is
   defined).
3. **Tag the commit**:
   ```bash
   git tag -a 2026.7.0 -m "Release 2026.7.0"
   git push origin 2026.7.0
   ```
4. **Publish** — GitHub Actions builds the release and publishes to PyPI
   (if configured).  Otherwise distribute as a source archive or wheel:
   ```bash
   uv build
   # dist/ contains .whl and .tar.gz
   ```

---

## 📋 Pre-Release Checklist

- [ ] All failing pages are resolved or documented as known issues
- [ ] `CHANGELOG.md` is up to date
- [ ] Default seed data in `schema.py` matches documentation
- [ ] `docs/` stubs are filled in for any new features
- [ ] Manual test checklist in [Test Cases](../development/test-cases.md) passes
- [ ] `.secrets` template in documentation is accurate

---

## 🔁 Hotfix Process

For critical bugs in a released version:
1. Branch from the release tag: `git checkout -b hotfix/2026.6.9.1 2026.6.9`.
2. Apply the fix.
3. Tag as `2026.6.9.1` and push.
