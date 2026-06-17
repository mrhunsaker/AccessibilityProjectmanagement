# Students

Navigate to **Production → Students** to manage student records and view
complete cross-job production history.

---

## 👤 Student Records

Each student record contains:

| Field | Description |
|-------|-------------|
| Last Name | Required |
| First Name | Required |
| School | Optional — used in reports and metadata filtering |
| Grade | Optional — used in reports |
| Preferred Formats | Free text (e.g. "Braille UEB Grade 2, Large Print 18pt") |
| Notes | Any additional context |

---

## ➕ Adding a Student

1. Click **+ Add Student**.
2. Fill in at least **First Name** and **Last Name**.
3. Click **Save**.

---

## 🔍 Searching Students

The search bar filters by last name, first name, and school simultaneously.
Toggle **Show Inactive** to include deactivated students.

---

## 📋 Student Detail View

Click **View** to open a student's detail page showing:

- Core student fields (school, grade, formats, notes)
- **All linked jobs** grouped by type (Braille, LP/eBraille, Tactile, 3-D Print)
- For each job: title, job type, due date, progress bar, and delivery status

---

## 🔗 Linking Jobs to Students

When creating or editing any job, use the **Student** dropdown to link it to a
student record.  The dropdown shows: `Last, First — School`.

---

## 📊 Job Counts

The student list shows the total job count for each student.  APM fetches
these in a single SQL query (`count_jobs_for_students()`) rather than per-row
to keep the list fast even with many students.

---

## 🗑️ Deactivating a Student

Click **Deactivate** in the student detail view.  This sets `active = 0` —
it is a **soft delete**.  All linked jobs and their history are preserved.
Deactivated students do not appear in job creation dropdowns but can be
restored directly in the database (`UPDATE student SET active = 1 WHERE id = ?`).

---

## 📈 Using Students in Reports

On the **Reports** page, use the **Student** dropdown to filter all job types
to a single student.  Combine with school, grade, status, and date range
filters for detailed per-student reporting.
