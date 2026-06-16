# API Reference

**RESTful API for programmatic access to APM.**

---

## 📡 Base URL

<http://localhost:8765/api>

## 🔐 Authentication
If `ACCESSMAN_API_AUTH_REQUIRED=1`:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8765/api/jobs
```

## 📋 Endpoints

### Jobs

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | /jobs | List all jobs |
| GET | /jobs/{id} | Get job details |
| POST | /jobs | Create new job |
| PUT | /jobs/{id} | Update job |
| DELETE | /jobs/{id} | Delete job |

### Students

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | /students | List all students |
| GET | /students/{id} | Get student details |
| POST | /students | Create new student |

### Inventory

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | /inventory | List all inventory items |
| GET | /inventory/{id} | Get item details |
| POST | /inventory | Add new item |
| PUT | /inventory/{id} | Update item |

### QA

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | /qa/validate | Run validation |
| GET | /qa/runs | List QA runs |

## 📤 Request Examples

### Create a braille job

```bash
curl -X POST http://localhost:8765/api/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "type": "braille",
    "title": "Math Textbook - Grade 10",
    "student_id": 123,
    "status": "pending"
  }'
```

### List All Jobs

```bash
curl http://localhost:8765/api/jobs \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 📥 Response Examples

### Job Object

```json
{
  "id": 1,
  "type": "braille",
  "title": "Math Textbook - Grade 10",
  "status": "pending",
  "created_at": "2026-06-16T10:00:00Z",
  "updated_at": "2026-06-16T10:00:00Z",
  "student": {
    "id": 123,
    "name": "Jane Doe"
  },
  "metadata": {
    "dublin_core": {...},
    "ebraille_profile": {...}
  }
}
```

