"""Basic smoke tests for db.queries."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'accessibility_mgr'))

import pytest
from db.schema import init_db, DB_PATH, get_conn
import db.queries as Q


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    import db.schema as _s
    monkeypatch.setattr(_s, "DB_PATH", db_file)
    monkeypatch.setattr(_s, "PRINTS_DIR", tmp_path / "prints_files")
    monkeypatch.setattr(_s, "FILES_DIR", tmp_path / "job_files")
    import db.queries as _q
    monkeypatch.setattr(_q, "PRINTS_DIR", tmp_path / "prints_files")
    monkeypatch.setattr(_q, "FILES_DIR", tmp_path / "job_files")
    init_db()
    yield


def test_filament_crud():
    fid = Q.add_filament("Bambu", "White", "PLA", quantity_g=500)
    fils = Q.list_filaments()
    assert len(fils) == 1
    assert fils[0]["brand"] == "Bambu"
    Q.deduct_filament(fid, 100)
    assert Q.list_filaments()[0]["quantity_g"] == 400
    Q.update_filament(fid, color="Black")
    assert Q.list_filaments()[0]["color"] == "Black"
    Q.delete_filament(fid)
    assert Q.list_filaments() == []


def test_braille_job_workflow():
    jid = Q.add_braille_job("Test Book", "literary", requester="Alice")
    job = Q.get_braille_job(jid)
    assert job["title"] == "Test Book"
    assert job["digitized"] == 0
    Q.complete_step("braille", jid, "digitized")
    assert Q.get_braille_job(jid)["digitized"] == 1
    events = Q.list_events_for_job("braille", jid)
    assert any(e["event_type"] == "STEP_COMPLETE" for e in events)
    Q.revert_step("braille", jid, "digitized")
    assert Q.get_braille_job(jid)["digitized"] == 0


def test_job_metadata():
    jid = Q.add_braille_job("Meta Test", "math")
    Q.set_job_metadata("braille", jid, "dc:title", "Math Book")
    assert Q.get_job_metadata("braille", jid, "dc:title") == "Math Book"
    meta = Q.list_job_metadata("braille", jid)
    assert meta["dc:title"] == "Math Book"
    Q.delete_job_metadata("braille", jid, "dc:title")
    assert Q.get_job_metadata("braille", jid, "dc:title") is None


def test_lp_job():
    jid = Q.add_lp_job("LP Test", "large_print", requester="Bob")
    assert Q.get_lp_job(jid)["job_type"] == "large_print"
    Q.complete_step("lp_ebraille", jid, "digitized")
    assert Q.get_lp_job(jid)["digitized"] == 1


def test_pipeline_and_qa_runs():
    run_id = Q.start_pipeline_run("Test Pipeline")
    Q.log_pipeline_step(run_id, "Step 1", "Pandoc", "pandoc a -o b", True, "ok")
    Q.finish_pipeline_run(run_id, "completed")
    runs = Q.list_pipeline_runs()
    assert runs[0]["status"] == "completed"
    steps = Q.list_pipeline_step_runs(run_id)
    assert steps[0]["step_name"] == "Step 1"

    Q.log_qa_run("EPUBCheck", "epubcheck x.epub", True, "No errors")
    qa = Q.list_qa_runs()
    assert qa[0]["tool_name"] == "EPUBCheck"


def test_material_categories():
    rows = Q.list_material_categories("filament_type")
    assert len(rows) > 0
    new_id = Q.add_material_category("filament_type", "wood", "Wood Fill", sort_order=99)
    rows2 = Q.list_material_categories("filament_type")
    assert any(r["value"] == "wood" for r in rows2)
    Q.set_material_category_active(new_id, 0)
    rows3 = Q.list_material_categories("filament_type")
    assert not any(r["value"] == "wood" for r in rows3)
