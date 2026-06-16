# Security Reference

## 🔐 Authentication
- **Algorithm**: PBKDF2-HMAC-SHA-256
- **Iterations**: 260,000
- **Salt**: 16 random bytes
- **Derived Key**: 32 bytes
- **Encoding**: Base64 (salt + derived key)

## 🔒 Secret Vault
- **Algorithm**: Fernet (AES-128-CBC with PKCS7 padding)
- **Key**: 32-byte URL-safe base64-encoded
- **Usage**: Encrypt/decrypt sensitive data (API keys, credentials)

## 🛡️ RBAC (Role-Based Access Control)
| Role | Description | Permissions |
|------|-------------|-------------|
| **Admin** | Full access | All features, all data |
| **Manager** | Production management | Create/edit jobs, view all data |
| **Technician** | Production execution | View/assign jobs, update status |
| **Viewer** | Read-only access | View all data, no modifications |

## 🔐 Best Practices
1. **Never commit `.secrets`** to version control
2. **Use strong, unique passwords**
3. **Rotate secrets periodically**
4. **Restrict file permissions** (`chmod 600 .secrets`)
5. **Enable API authentication** for production
6. **Use HTTPS** in production (via reverse proxy)
