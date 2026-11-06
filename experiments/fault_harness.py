"""Harness separato per arresti controllati del backend compilato.

Compilazione: build/package-venv/Scripts/python -m nuitka --standalone
    --msvc=14.3 --output-dir=build/fault-harness experiments/fault_harness.py
Uso: fault_harness.exe STORAGE SOURCE before|after|normal
"""
import os
import sys

from local_document_search.application.errors import ResourceFailure, StorageFailure
from local_document_search.interfaces.composition import compose_persistent_application


def main():
    storage, source, phase = sys.argv[1:]
    with compose_persistent_application(storage) as app:
        state = app.status.execute()
        if state.active_directory is None:
            app.select_directory.execute(source)
            app.synchronize.execute()
            return
        if phase in ("before", "after", "race"):
            repo = app.snapshots._repo
            original = repo._commit

            def crash():
                if phase == "before":
                    os._exit(71)
                if phase == "race":
                    print("committing", flush=True)
                    original()
                    return
                original()
                os._exit(72)

            repo._commit = crash
        if phase == "full":
            repo = app.snapshots._repo
            pages = repo._db.execute("PRAGMA page_count").fetchone()[0]
            repo._db.execute(f"PRAGMA max_page_count={pages}")
        if phase == "memory":
            app.snapshots.save_candidate = lambda _: (_ for _ in ()).throw(MemoryError())
        if phase == "write":
            app.snapshots.save_candidate = lambda _: (_ for _ in ()).throw(StorageFailure("test"))
        try:
            app.synchronize.execute()
        except ResourceFailure:
            if phase in ("full", "memory"):
                os._exit(73)
            raise
        except StorageFailure:
            if phase == "write":
                os._exit(74)
            raise


if __name__ == "__main__":
    main()
