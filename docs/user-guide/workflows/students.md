# Students

Navigate to **Production → Students** to manage student records and view
complete cross-job production history.

---

## Student Records

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

## Adding a Student

1. Click **+ Add Student**.
2. Fill in at least **First Name** and **Last Name**.
3. Click **Save**.

---

## Bulk Importing Students from CSV

Next to **+ Add Student** there is a **+ BULK IMPORT** button for adding
many students at once from a comma-separated (`.csv`) file.

### 1. Download the Template

Click **+ BULK IMPORT** and then **Download Template** to fetch
`students_template.csv`. It is generated in memory with the expected columns
and two example rows you can overwrite.

### 2. Prepare Your File

The template uses these columns (header row required):

| Column | Required | Notes |
|--------|----------|-------|
| `last_name` | Yes | Used in the business key |
| `first_name` | Yes | Used in the business key, together with last name |
| `school` | No | |
| `grade` | No | |
| `preferred_formats` | No | e.g. "Braille UEB Grade 2, Large Print 18pt" |
| `notes` | No | |

Any row with a **blank `first_name` or `last_name`** is skipped and reported
as a row-level error. Empty cells, and the tokens `nan`, `none`, `null`, `-`,
`n/a`, and `na`, are treated as blank.

### 3. Select the File

Click **Choose CSV File** to open a native file picker and select your `.csv`.

### 4. Review the Preview

Before anything is written, APM shows a preview grouped into three buckets:

- **To Add** — rows that qualify for insertion
- **To Skip** — duplicates, either repeated within the file (first occurrence
  wins) or already present in the database
- **Errors** — rows missing a first or last name

Students are de-duplicated on the combined `(first_name, last_name)` business
key, matched **case-insensitively**. **Duplicates are always skipped and never
overwrite existing records.**

### 5. Commit

Click **Confirm Import** to insert every **To Add** row in a single
transaction. The result reports how many were added, skipped, and errored.

---

## Searching Students

The search bar filters by last name, first name, and school simultaneously.
Toggle **Show Inactive** to include deactivated students.

---

## Student Detail View

Click **View** to open a student's detail page showing:

- Core student fields (school, grade, formats, notes)
- **All linked jobs** grouped by type (Braille, LP/eBraille, Tactile, 3-D Print)
- For each job: title, job type, due date, progress bar, and delivery status

---

## Linking Jobs to Students

When creating or editing any job, use the **Student** dropdown to link it to a
student record.  The dropdown shows: `Last, First — School`.

---

## Job Counts

The student list shows the total job count for each student.  APM fetches
these in a single SQL query (`count_jobs_for_students()`) rather than per-row
to keep the list fast even with many students.

---

## Deactivating a Student

Click **Deactivate** in the student detail view.  This sets `active = 0` —
it is a **soft delete**.  All linked jobs and their history are preserved.
Deactivated students do not appear in job creation dropdowns but can be
restored directly in the database (`UPDATE student SET active = 1 WHERE id = ?`).

---

## Using Students in Reports

On the **Reports** page, use the **Student** dropdown to filter all job types
to a single student.  Combine with school, grade, status, and date range
filters for detailed per-student reporting.
