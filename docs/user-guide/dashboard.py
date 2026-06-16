# Dashboard

**Central hub for monitoring and managing your accessibility production workflows.**

---

## 📊 Layout Overview

```mermaid
graph TD
    A[Dashboard] --> B[Active Jobs Card]
    A --> C[Low Stock Alerts Card]
    A --> D[Recent Activity Card]
    A --> E[Quick Create Panel]
    A --> F[Upcoming Deadlines Widget]


## 🎨 Dashboard Sections
### 📌 Active Jobs

- Purpose: Track jobs currently in progress
- Features:
  - Color-coded by status (Pending, In Progress, Completed, Overdue)
  - Click to view job details
  - Filter by type (Braille, Large Print, etc.)
- Columns:
  - Job ID
  - Title
  - Type
  - Student
  - Due Date
  - Status
  - Assigned To

### ⚠️ Low Stock Alerts

- Purpose: Warn about inventory items below minimum thresholds
- Features:
-  Real-time updates
- Direct links to inventory management
- Configurable thresholds

- Displayed Items:
  - Filament (3D printing)
  - Braille paper
  - Electronics components

### 🕒 Recent Activity

- Purpose: Timeline of recent system events
- Features:
  - Last 50 events
  - Filter by type (Job Created, File Ingested, QA Run, etc.)
  - Click to view full details

- Event Types:
  - Job lifecycle changes
  -File operations
  -Inventory transactions
  -User actions

### ⚡ Quick Create

- Purpose: One-click job creation
- Features:
  - Dropdown for job type selection
  - Minimal required fields
  - Auto-fills common defaults

- Supported Types:
  - Braille Job
  - Large Print Job
  - eBraille Job
  - EPUB3/DAISY Job
  - Tactile Graphics Job
  - 3-D Print Job

### 📅 Upcoming Deadlines

- Purpose: Jobs due in the next 7 days
- Features:
  - Sorted by due date
  - Color-coded urgency (Green = >3 days, Yellow = 1-3 days, Red = <24 hours)
  - Click to view job details


### 🔧 Customization

- Widget Visibility
  - Toggle widgets on/off in Admin → Dashboard Settings:
   -  Active Jobs
   - Low Stock Alerts
   - Recent Activity
   - Quick Create
   - Upcoming Deadlines
- Layout Options
  - Grid Density: Compact or Spacious
  - Theme: Light/Dark/System
  - Color Scheme: Primary and accent colors

### 💡 Pro Tips

- Pin Important Jobs: Star jobs to keep them at the top of lists
- Bulk Actions: Select multiple jobs to apply status changes
 - Export Views: Download current view as CSV
- Saved Filters: Save common filter combinations
- Keyboard Shortcuts:
  - Ctrl+K: Global search
  - Ctrl+N: New job
  - Ctrl+R: Refresh data


