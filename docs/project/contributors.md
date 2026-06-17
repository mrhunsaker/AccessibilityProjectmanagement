# Contributing

Contributions are welcome.  This page explains how to get involved.

---

## 🤝 How to Contribute

1. **Fork** the repository on GitHub.
2. Create a **feature branch**: `git checkout -b feature/my-improvement`.
3. Make changes, following the conventions below.
4. **Commit** with a descriptive message.
5. Open a **Pull Request** targeting `main`.

---

## 🧭 Code Conventions

- **SQL**: All queries in `db/queries.py` using `?` placeholders.
- **UI**: NiceGUI components using Tailwind classes from the existing palette.
- **Services**: Stateless or clearly-scoped singletons; no global mutable state
  outside `services/singletons.py`.
- **Imports**: Absolute imports (`from accessibility_mgr.db import queries as Q`).
- **Type hints**: Required for all new public functions.

---

## 🐛 Reporting Issues

Open a GitHub Issue with:
- APM version / commit hash
- Python version (`python --version`)
- Steps to reproduce
- Expected vs actual behaviour
- Relevant log output

---

## 💡 Feature Requests

Open a GitHub Discussion under the **Ideas** category.  Include:
- The accessibility workflow problem you are solving
- How your proposal fits the existing data model
- Any UI wireframe or description

---

## 📜 License

By contributing you agree that your code will be released under the
[MIT License](../license.md).
