"""Verifica recovery e lock con l'harness compilato in storage temporaneo."""
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from local_document_search.application.contracts import SearchRequest
from local_document_search.interfaces.composition import compose_persistent_application


def main(command):
    for phase, expected_exit, expected_term in (("before", 71, "alpha"),
                                                  ("after", 72, "bravo"),
                                                  ("full", 73, "alpha"),
                                                  ("memory", 73, "alpha"),
                                                  ("write", 74, "alpha")):
        with tempfile.TemporaryDirectory(prefix="lds-fault-") as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            document = source / "a.txt"
            document.write_text("alpha", encoding="utf-8")
            storage = base / "storage"
            with compose_persistent_application(storage) as app:
                state = app.select_directory.execute(str(source))
                app._lifecycle.jobs.wait(state.job.job_id)
                old = app.status.execute().active_snapshot_id
            document.write_text("bravo " * (10000 if phase == "full" else 2), encoding="utf-8")
            child = subprocess.run([*command, str(storage), str(source), phase], timeout=30)
            assert child.returncode == expected_exit, (phase, child.returncode)
            with compose_persistent_application(storage) as app:
                state = app.status.execute()
                assert state.active_snapshot_id == (old if phase == "before" else state.active_snapshot_id)
                response = app.search.execute(SearchRequest(expected_term))
                assert response.total_matches == 1
                other = "bravo" if expected_term == "alpha" else "alpha"
                assert app.search.execute(SearchRequest(other)).total_matches == 0
                assert response.snapshot_id == state.active_snapshot_id
                assert app.get_document.execute(response.results[0].document_id,
                                                response.snapshot_id).extracted_text.strip() == (
                    "alpha" if phase != "after" else "bravo bravo")
            print(phase, "PASS", flush=True)

    for delay in (0, 0.001, 0.01):
        with tempfile.TemporaryDirectory(prefix="lds-race-") as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            document = source / "a.txt"
            document.write_text("alpha", encoding="utf-8")
            storage = base / "storage"
            with compose_persistent_application(storage) as app:
                state = app.select_directory.execute(str(source))
                app._lifecycle.jobs.wait(state.job.job_id)
            document.write_text("bravo bravo", encoding="utf-8")
            child = subprocess.Popen([*command, str(storage), str(source), "race"],
                                     stdout=subprocess.PIPE, text=True)
            try:
                assert child.stdout.readline().strip() == "committing"
                time.sleep(delay)
                child.kill()
                child.wait(timeout=10)
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=10)
            with compose_persistent_application(storage) as app:
                alpha = app.search.execute(SearchRequest("alpha"))
                bravo = app.search.execute(SearchRequest("bravo"))
                assert (alpha.total_matches, bravo.total_matches) in ((1, 0), (0, 1))
                result = alpha if alpha.total_matches else bravo
                assert result.snapshot_id == app.status.execute().active_snapshot_id
            print("race", delay, "PASS", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
