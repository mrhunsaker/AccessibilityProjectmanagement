# Users & Roles

APM uses a lightweight user switcher backed by environment variables.  There
is no sign-up flow — accounts are defined in `.secrets` before the app starts.

---

## 👤 Defining User Accounts

Add one `ACCESSMAN_USER_N` variable per account in `.secrets`:

```ini
ACCESSMAN_USER_1=alice:Administrator:true
ACCESSMAN_USER_2=bob:Operator:false
ACCESSMAN_USER_3=carol:Reviewer
```

Format: `username:role[:is_admin]`

- `username` — display name used in the user switcher and audit events.
- `role` — free-text role label shown in the security dashboard.
- `is_admin` — `true`/`1`/`yes` grants admin capabilities (optional, defaults false).

If no `ACCESSMAN_USER_N` variables are set, a single placeholder account
(`local_operator / Operator`) is created with a warning in the log.

---

## 🔐 Login

Authentication uses a **single shared password** stored as a
PBKDF2-HMAC-SHA-256 hash in `ACCESSMAN_PASSWORD_HASH`.  All accounts share
this password.  See [Configuration](../getting-started/configuration.md) for
hash generation instructions.

---

## 🔄 Switching Users

After login, click the **person_off** icon in the top-right toolbar to switch
the active account.  This updates `AuthService.current_user` (in-memory) but
does not require re-authentication.

---

## 🛡️ RBAC Roles

The `RBACService` defines three built-in roles:

| Role | Permissions |
|------|-------------|
| `administrator` | `qa.execute`, `qa.review`, `governance.manage`, `workflow.manage`, `analytics.view`, `rbac.manage` |
| `operator` | `qa.execute`, `workflow.manage`, `analytics.view` |
| `reviewer` | `qa.review`, `analytics.view` |

Role assignments are visible in **Admin → Security Dashboard**.

---

## 🔒 Session Management

Sessions are managed by NiceGUI's `app.storage.user` backed by the
`STORAGE_SECRET` key.  Clearing the session (logout) calls
`nicegui_app.storage.user.clear()` which invalidates all stored state
including the `authenticated` flag.

Session data is **not** shared across different browser tabs or devices.
