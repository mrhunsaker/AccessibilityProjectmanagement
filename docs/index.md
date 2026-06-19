# Accessibility Project Management

**Professional workflow and inventory platform for accessibility production teams.**

---

## 🎯 Overview

The **Accessibility Project Management (APM)** system is a **NiceGUI-based local web application** designed to streamline and manage the production of accessible materials for educational and professional environments. It provides comprehensive workflow tracking, file management, inventory control, and quality assurance for:

- **Braille transcription and embossing**
- **Large print production**
- **eBraille digital formats**
- **EPUB3 and DAISY accessible e-books**
- **Tactile graphics (thermoform, hand-tooled, embossed)**
- **3-D printing for accessibility aids**

APM combines **job management, file ingestion, metadata tracking, QA tooling integration, and consumables inventory** into a single, cohesive platform backed by **SQLite** for local data persistence.

---

## ✨ Key Features

### 📋 Production Workflow Management
- **Dedicated workflow pages** for each production type
- **Step-by-step tracking** with completion, reversion, and delivery capture
- **Event logging** for full auditability
- **Student record linkage** for cross-job history

### 📁 File Ingestion & Preservation
- **Drag-and-drop or path-based ingestion**
- **Automatic SHA-256 checksums** and PREMIS-style event logging
- **File-use classification** and provenance tracking
- **Organized storage** in `artifacts/<Project Title>/...`

### 📊 Search & Reporting
- **Global search** across jobs, metadata, students, files, and events
- **Exact checksum matching** for file identification
- **Filterable reports** by school, grade, type, status, and date range
- **CSV export** for all reports

### 📦 Inventory Control
- **Filament tracking** (brand, color, type, diameter, quantity, cost, supplier)
- **Braille paper management** (type, size, label, quantity, supplier)
- **Electronics inventory** (configurable categories for components)
- **Low-stock warnings** and transaction history

### ✅ Quality Assurance
- **Integration with industry-standard tools**: DAISY Ace, EPUBCheck, Liblouis, BRLTTY, Pandoc, DAISY Pipeline 2
- **QA run storage** in database, linked to jobs

### 🔗 Provenance & Lineage
- **Full event history** for all operations
- **Mermaid-based lineage viewer** for file-to-job relationships

### 🔐 Security & Access Control
- **PBKDF2-HMAC-SHA-256 password hashing**
- **Fernet encryption** for sensitive data
- **Role-Based Access Control (RBAC)** for multi-user environments

### 📡 API
- **RESTful API** mounted at `/api`
- **Optional authentication** via API keys

---
## 🚀 Getting Started

New to APM? Follow our **[Installation Guide](getting-started/installation.md)** to set up your environment.

---
## 📖 Documentation Structure

| Section | Description |
|---------|-------------|
| **[Getting Started](getting-started/index.md)** | Installation, configuration, and initial setup |
| **[User Guide](user-guide/index.md)** | Comprehensive guide to using APM features |
| **[Administration](administration/index.md)** | Admin tasks, security, backups, and API |
| **[Development](development/index.md)** | Architecture, contributing, and extending APM |
| **[Operations](operations/index.md)** | Deployment, monitoring, and scaling |
| **[Reference](reference/index.md)** | Environment variables, tools, database schema, and security |
| **[Project](project/index.md)** | Roadmap, release process, and contributing guidelines |
| **[Support](support/index.md)** | FAQ, troubleshooting, and contact information |

---
## 🤝 Community & Support

- **Issues**: [GitHub Issues](https://github.com/mrhunsaker/AccessibilityProjectManagement/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mrhunsaker/AccessibilityProjectManagement/discussions)
- **Email**: [github@mail.hunsakerweb.com](mailto:github@mail.hunsakerweb.com)

---
## 📜 License

APM is released under the **[MIT License](license.md)**.

---
*Empowering accessibility production teams with professional-grade workflow management.*
