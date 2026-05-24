# Security Policy

## Supported Versions

Only the latest release on the `main` branch receives security fixes.

| Version         | Supported |
| --------------- | --------- |
| latest (`main`) | ✅ Yes    |
| older tags      | ❌ No     |

---

## Scope

Braille & Maker Studio is a **local desktop application**. It stores all data
in a SQLite file on the user's own machine and does not transmit data over a
network. The attack surface is therefore limited, but the following concerns
are still in scope:

- **SQL injection** via user-supplied input passed to the database layer
- **Path traversal** when copying user-supplied 3-D print file paths into
  `prints_files/`
- **Dependency vulnerabilities** in `textual` or any future added dependency
- **Unsafe deserialization** if any future feature loads external data files

The following are explicitly **out of scope**:

- Attacks that require physical access to the machine where the app is running
- Social engineering of maintainers
- Denial-of-service against a local process

---

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Instead, report them privately by one of these methods:

1. **GitHub private vulnerability reporting** (preferred):  
   Go to the repository → Security → "Report a vulnerability"
2. **Email**: send details to `github@mail.hunsakerweb.com`

Include:

- A description of the vulnerability and its potential impact
- Steps to reproduce (a minimal script or sequence of UI actions)
- Any suggested fix, if you have one

You will receive an acknowledgement within **3 business days** and a resolution
timeline within **10 business days**. We will credit reporters in the release
notes unless they request anonymity.

---

## Best Practices for Users

- Keep your Python environment and dependencies up to date:

  ```bash
  uv sync --upgrade
  ```

- Back up `project_manager.db` regularly — it contains all your inventory and
  job data.
- Do not place the `project_manager.db` file in a publicly accessible location
  (e.g. a shared web folder).
- On multi-user systems, restrict read/write access to the project directory to
  your own account.
