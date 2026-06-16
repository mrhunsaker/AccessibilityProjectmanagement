# First Steps

**Create your first project and start managing accessibility workflows.**

---

## 🚀 Quick Start Guide

### 1. Log In
1. Navigate to [http://localhost:8765](http://localhost:8765)
2. Enter your password (configured in `.secrets`)
3. You'll land on the **Dashboard**

---

## 📋 Create Your First Job

### Braille Job Example
1. Click **"Braille Jobs"** in the sidebar
2. Click **"New Job"** button
3. Fill in the form:
   - **Title**: "Math Textbook - Chapter 1"
   - **Student**: Select or create a student record
   - **Due Date**: Set deadline
   - **Priority**: Medium/High
4. Click **"Create"**

### Required Fields
   Field | Description | Example |
 |-------|-------------|---------|
 | Title | Job identifier | "Science Quiz - Braille" |
 | Student | Recipient | Jane Doe (Grade 10) |
 | Type | Production type | Braille |
 | Source File | Upload or path | `~/documents/science_quiz.pdf` |

---

## 📁 File Ingestion Workflow

1. **Upload Files**:
   - Drag & drop into the ingestion page
   - Or specify a local path

2. **Automatic Processing**:
   - SHA-256 checksum calculated
   - File size and MIME type recorded
   - Stored in `artifacts/<Project Title>/`

3. **Classification**:
   - Select file type (Source, Output, Reference)
   - Link to specific job

---

## 🎯 Dashboard Overview

### Widgets
- **Active Jobs**: Currently in-progress workflows
- **Low Stock**: Inventory items needing replenishment
- **Recent Activity**: Timeline of recent events
- **Quick Actions**: One-click job creation

### Navigation
- **Overview**: Dashboard and reports
- **Production**: All workflow types
- **Inventory**: Consumables management
- **Metadata & Files**: File and metadata tools
- **QA & Automation**: Validation tools
- **Admin**: Configuration and settings

---
## ✅ Next Actions

1. [ ] Create 3-5 sample jobs for each workflow type
2. [ ] Add your inventory items (filament, paper, etc.)
3. [ ] Configure external tools in `tools.ini`
4. [ ] Test the backup system
