# Security

**Comprehensive security guide for Accessibility Project Management.**

---

## 🔒 Overview

Security is **paramount** in APM, especially when handling sensitive student data and accessibility materials. This guide covers all aspects of securing your APM instance, from authentication and authorization to data protection and audit compliance.

---

## 🛡️ Security Architecture

APM employs a **multi-layered security approach**:

```mermaid
graph TD
    A[Client] -->|HTTPS| B[Reverse Proxy]
    B -->|HTTP| C[APM Application]
    C --> D[Authentication Layer]
    D --> E[Authorization Layer]
    E --> F[Data Access Layer]
    F --> G[Data Storage: SQLite]
    G --> H[File Storage]
    
    D --> I[Session Management]
    D --> J[Password Hashing: PBKDF2]
    E --> K[Role-Based Access Control]
    F --> L[Data Encryption: Fernet]
    G --> M[SQLite Encryption]
    H --> N[File System Permissions]
    
    O[.secrets] --> C
    P[tools.ini] --> C
    Q[Audit Logs] --> F
```

---

## 🔐 Authentication

### Password Security

APM uses **PBKDF2-HMAC-SHA-256** for password hashing with:

- **260,000 iterations** (computationally intensive to prevent brute force)
- **Random 16-byte salt** (unique for each password)
- **32-byte derived key** (256 bits of security)
- **Base64 encoding** (salt + derived key stored together)

#### Password Hash Generation

Generate a secure password hash:

```bash
python -c "
import hashlib, os, base64
password = b'your_secure_password_here'
salt = os.urandom(16)
dk = hashlib.pbkdf2_hmac('sha256', password, salt, 260000)
print('ACCESSMAN_PASSWORD_HASH=' + base64.b64encode(salt + dk).decode())
"
```

> **⚠️ Security Note**: 
>
> - Never use simple or dictionary passwords
> - Never reuse passwords across systems
> - Generate a **new hash** for each deployment
> - Store the `.secrets` file securely

#### Legacy SHA-256 Support

For backward compatibility, APM still accepts **64-character hex SHA-256 hashes**, but this triggers a **deprecation warning**. Use PBKDF2 for all new deployments.

**Legacy hash generation** (not recommended):

```bash
python -c "import hashlib; print(hashlib.sha256(b'your_password'.encode()).hexdigest())"
```

### Session Management

APM uses **NiceGUI's session system** with:

- **STORAGE_SECRET**: Encrypts session data (must be strong and unique)
- **Session Timeout**: Configurable inactivity timeout (default: 30 minutes)
- **Session Isolation**: Each user has isolated session data

#### Generating STORAGE_SECRET

```bash
python -c "import secrets; print('STORAGE_SECRET=' + secrets.token_urlsafe(32))"
```

**Requirements**:

- At least 32 characters
- Cryptographically random
- Unique for each deployment
- Never committed to version control

### Login Process

1. User submits username and password
2. APM:
  - Validates input (rejects empty passwords)
  - Looks up password hash from configuration
  - Verifies password using PBKDF2 with stored salt
  - Checks for account lockout
  - Creates session on success
3. Session stored in:
  - **Server-side**: Encrypted session data
  - **Client-side**: Session cookie (HttpOnly, Secure if HTTPS)

### Failed Login Handling

- **Max Attempts**: Configurable (default: 5)
- **Lockout Duration**: Configurable (default: 15 minutes)
- **IP Tracking**: Tracks failed attempts by IP
- **Account Lockout**: Temporarily disables account after max attempts
- **IP Blocking**: Optionally block IPs with too many failed attempts

### Two-Factor Authentication (2FA)

APM supports **Time-based One-Time Password (TOTP)** 2FA:

#### Enabling 2FA

1. Navigate to **Admin → Settings → Security**
2. Enable **Two-Factor Authentication**
3. Configure:
  - **2FA Method**: TOTP (default)
  - **Enforcement**: Optional or Required
  - **Issuer**: Organization name for authenticator apps
4. Users must configure 2FA on next login

#### User 2FA Setup

1. User logs in with password
2. If 2FA is enabled and not configured:
  - User is prompted to set up 2FA
  - User scans QR code with authenticator app (Google Authenticator, Authy, etc.)
  - User enters verification code
3. 2FA is now required for all future logins

#### Recovery Codes

- Users receive **10 recovery codes** during setup
- Each code can be used **once** to bypass 2FA
- Codes are **single-use** and **not regenerated** automatically
- Admins can generate new recovery codes for users

---

## 🔑 Secret Management

### Secret Vault Service

APM includes a **SecretVaultService** for encrypting sensitive data using **Fernet symmetric encryption** (AES-128 in CBC mode with PKCS7 padding).

#### Fernet Key Generation

```bash
python -c "from cryptography.fernet import Fernet; print('ACCESSMAN_VAULT_KEY=' + Fernet.generate_key().decode())"
```

**Requirements**:

- 32 URL-safe base64-encoded bytes
- Unique for each deployment
- Never committed to version control
- Rotated periodically

#### Using the Vault

```python
from accessibility_mgr.security.secret_vault import SecretVaultService

# Initialize vault (automatically uses ACCESSMAN_VAULT_KEY)
vault = SecretVaultService()

# Store a secret
vault.store_secret(name="api_key", value="sk_live_abc123...")

# Retrieve a secret
api_key = vault.retrieve_secret("api_key")

# List all secrets
secrets = vault.list_secrets()
```

#### Secret Types

Store any sensitive data in the vault:

- API keys for external services
- Database credentials
- Encryption keys
- Service account tokens
- Configuration secrets

### Environment Variables

APM loads sensitive configuration from `.secrets` file:

```ini
# .secrets - NEVER COMMIT TO VERSION CONTROL

# Authentication
STORAGE_SECRET=your_storage_secret_here
ACCESSMAN_PASSWORD_HASH=your_pbkdf2_password_hash_here
ACCESSMAN_VAULT_KEY=your_fernet_key_here

# API
ACCESSMAN_API_AUTH_REQUIRED=1
ACCESSMAN_API_KEY=your_api_key_here

# Database
ACCESSMAN_DB_PATH=/var/lib/accessibility_mgr/database.db

# Development only (DANGER)
ACCESSMAN_UNPROTECTED=0
```

> **⚠️ Critical**: 
>
> - `.secrets` must be in the **repository root** (not inside `accessibility_mgr/`)
> - File permissions should be **600** (owner read/write only)
> - Never commit `.secrets` to version control
> - Exclude from backups if they contain sensitive data

---

## 🛡️ Authorization

### Role-Based Access Control (RBAC)

APM uses a **flexible RBAC system** to control user access.

#### Default Roles


| Role                  | Description           | Permissions                                       |
| --------------------- | --------------------- | ------------------------------------------------- |
| **Admin**             | Full system access    | All permissions                                   |
| **Manager**           | Production management | Create/edit jobs, view all data, manage inventory |
| **Technician**        | Production execution  | View/assign jobs, update status, record time      |
| **Viewer**            | Read-only access      | View all data, no modifications                   |
| **QA Specialist**     | Quality assurance     | Run QA tools, view QA results, create QA profiles |
| **Inventory Manager** | Inventory control     | Manage inventory, view reports, process orders    |


#### Permission Categories


| Category      | Description          | Example Permissions                         |
| ------------- | -------------------- | ------------------------------------------- |
| **Jobs**      | Job management       | Create, Read, Update, Delete, Assign        |
| **Inventory** | Inventory control    | View, Add, Edit, Delete, Transact           |
| **QA**        | Quality assurance    | Run tools, View results, Create profiles    |
| **Reports**   | Reporting            | View, Create, Edit, Delete, Export          |
| **Users**     | User management      | View, Create, Edit, Delete, Deactivate      |
| **Settings**  | System configuration | View, Edit                                  |
| **API**       | API access           | Access, Create tokens, Manage keys          |
| **Admin**     | Administration       | Manage roles, View logs, System maintenance |


#### Custom Roles

Create roles tailored to your organization:

1. Navigate to **Admin → Roles & Permissions**
2. Click **Create Role**
3. Define **permissions** for each category
4. Assign to users as needed

### Permission Inheritance

Permissions can be **inherited** from other roles:

- Create a **base role** with common permissions
- Create **specialized roles**
