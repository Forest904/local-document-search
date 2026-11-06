"""Widget e coordinamento asincrono tramite i soli contratti applicativi."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QSplitter,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from local_document_search.application.contracts import JobState, SearchField, SearchRequest
from local_document_search.application.errors import SnapshotUnavailable


PRIVACY = (
    "L'elaborazione avviene sul dispositivo. Il testo estratto viene salvato localmente "
    "e può restare disponibile anche quando il file sorgente è assente. "
    "Elimina dati locali rimuove i dati applicativi, senza modificare i documenti originali."
)


class SearchWindow(QMainWindow):
    def __init__(self, factory, opener):
        super().__init__()
        self.factory, self.opener = factory, opener
        self.session = None
        self.state = None
        self.coordinator = ThreadPoolExecutor(max_workers=1, thread_name_prefix="desktop")
        self.pending = []
        self.control_pending = False
        self.poll_pending = False
        self.closing = self.closed = False
        self.generation = self.detail_generation = 0
        self.response = None
        self.offset = 0
        self.seen_terminal = set()
        self.spinner_frame = 0
        self.setWindowTitle("Local Document Search")
        self.resize(1100, 720)
        body = QWidget()
        layout = QVBoxLayout(body)
        top = QHBoxLayout()
        self.choose = QPushButton("Scegli cartella…")
        self.directory = QLabel("Nessuna cartella selezionata — TXT, Markdown e PDF")
        self.directory.setWordWrap(True)
        self.sync = QPushButton("Sync")
        for widget in (self.choose, self.directory, self.sync):
            top.addWidget(widget)
        top.setStretch(1, 1)
        layout.addLayout(top)
        row = QHBoxLayout()
        self.query = QLineEdit()
        self.query.setPlaceholderText('Termini in AND o frasi: machine "deep learning" — Invio per cercare')
        self.field = QComboBox()
        for label, value in (("Entrambi", SearchField.BOTH), ("Nome", SearchField.FILENAME),
                             ("Contenuto", SearchField.CONTENT)):
            self.field.addItem(label, value)
        row.addWidget(self.query, 1)
        row.addWidget(self.field)
        layout.addLayout(row)
        self.results = QTreeWidget()
        self.results.setHeaderLabels(["Nome", "Percorso relativo", "Formato"])
        self.results.setRootIsDecorated(False)
        self.results.setColumnWidth(0, 180)
        self.results.setColumnWidth(1, 260)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Seleziona un risultato per leggere il testo completo")
        split = QSplitter()
        split.addWidget(self.results)
        split.addWidget(self.preview)
        layout.addWidget(split, 1)
        pages = QHBoxLayout()
        self.previous = QPushButton("Precedente")
        self.next = QPushButton("Successiva")
        self.count = QLabel("Nessuna ricerca")
        self.open_file = QPushButton("Apri file")
        for widget in (self.previous, self.count, self.next, self.open_file):
            pages.addWidget(widget)
        pages.setStretch(1, 1)
        layout.addLayout(pages)
        self.status = QLabel("Pronto")
        self.status.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.hide()
        self.message = QLabel()
        self.message.setWordWrap(True)
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        layout.addWidget(self.message)
        bottom = QHBoxLayout()
        self.privacy = QPushButton("Informativa dati locali")
        self.job_details = QPushButton("Dettagli ultimo job")
        self.start = QPushButton("Continua")
        self.clear = QPushButton("Elimina dati locali…")
        bottom.addWidget(self.privacy)
        bottom.addWidget(self.job_details)
        bottom.addStretch()
        bottom.addWidget(self.start)
        bottom.addWidget(self.clear)
        layout.addLayout(bottom)
        self.setCentralWidget(body)
        for label in (self.directory, self.status, self.count):
            label.setTextFormat(Qt.TextFormat.PlainText)
        self.message.setText(PRIVACY)
        self.choose.clicked.connect(self.select_directory)
        self.sync.clicked.connect(self.request_sync)
        self.query.returnPressed.connect(lambda: self.search(0))
        self.query.textChanged.connect(self.invalidate)
        self.field.currentIndexChanged.connect(self.invalidate)
        self.results.currentItemChanged.connect(self.show_document)
        self.previous.clicked.connect(lambda: self.search(max(0, self.offset - 50)))
        self.next.clicked.connect(lambda: self.search(self.offset + 50))
        self.open_file.clicked.connect(self.open_selected)
        self.clear.clicked.connect(self.clear_data)
        self.start.clicked.connect(self.initialize)
        self.privacy.clicked.connect(lambda: QMessageBox.information(self, "Dati locali", PRIVACY))
        self.job_details.clicked.connect(self.show_job_report)
        self.last_job_report = None
        self.check_timer = QTimer(self)
        self.check_timer.setSingleShot(True)
        self.check_timer.setInterval(1500)
        self.check_timer.timeout.connect(lambda: self.sync.setText("Sync"))
        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.refresh_controls()

    def watch(self, future, success, failure=None):
        self.pending.append((future, success, failure or self.error))

    def error(self, exc):
        if isinstance(exc, SnapshotUnavailable):
            self.message.setText("Versione non disponibile. Ripeti la ricerca; se necessario premi Sync.")
        else:
            self.message.setText(f"{type(exc).__name__}: {exc}")

    def control(self, operation, success):
        self.control_pending = True
        self.refresh_controls()

        def complete(value):
            self.control_pending = False
            success(value)
            self.refresh_controls()

        def failed(exc):
            self.control_pending = False
            self.error(exc)
            self.refresh_controls()

        self.watch(self.coordinator.submit(operation), complete, failed)

    def initialize(self):
        self.start.setEnabled(False)
        self.message.clear()

        def create():
            session = self.factory()
            try:
                try:
                    state = session.initialize.execute()
                except SnapshotUnavailable as exc:
                    # Storage incompatibile senza sorgente: lascia disponibili selezione e pulizia.
                    return session, session.status.execute(), exc
                return session, state, None
            except Exception:
                session.close()
                raise

        def ready(value):
            self.session, state, error = value
            self.start.hide()
            self.apply_state(state)
            if error:
                self.message.setText("Indice incompatibile senza sorgente. Scegli una cartella per ricostruirlo o elimina i dati locali.")

        self.control(create, ready)

    def invalidate(self, *_):
        self.generation += 1
        self.detail_generation += 1
        self.response = None
        self.results.clear()
        self.preview.clear()
        self.count.setText("Premi Invio per cercare")
        self.refresh_controls()

    def refresh_controls(self):
        busy = self.control_pending or self.closing
        job = self.state.job if self.state else None
        running = job is not None and job.status in (JobState.PENDING, JobState.RUNNING)
        ready = self.session is not None and not busy
        self.choose.setEnabled(ready and not running)
        self.clear.setEnabled(ready and not running)
        self.sync.setEnabled(ready and bool(self.state and self.state.active_directory) and not running)
        searchable = ready and bool(self.state and self.state.search_available)
        self.query.setEnabled(searchable)
        self.field.setEnabled(searchable)
        self.results.setEnabled(searchable)
        self.previous.setEnabled(searchable and self.response is not None and self.offset > 0)
        self.next.setEnabled(searchable and self.response is not None
                             and self.offset + 50 < self.response.total_matches)
        self.open_file.setEnabled(searchable and self.results.currentItem() is not None)
        self.start.setEnabled(self.session is None and not busy)
        self.job_details.setEnabled(self.last_job_report is not None)

    def show_job_report(self):
        report = self.last_job_report
        if report is None:
            return
        lines = ["Report completo" if report.complete else "Report incompleto",
                 f"Esclusi: {report.excluded}",
                 f"Snapshot pubblicato: {report.published_snapshot_id or 'nessuno'}"]
        lines.extend(f"{item.category} · {item.relative_path or 'job'} · {item.reason}"
                     for item in report.diagnostics)
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Dettagli ultimo job")
        dialog.setText("\n".join(lines[:3]))
        dialog.setDetailedText("\n".join(lines[3:]) or "Nessuna diagnostica")
        dialog.exec()

    def apply_state(self, state):
        if self.state and self.state.active_directory != state.active_directory:
            self.invalidate()
        if state.active_directory is None and self.state and self.state.active_directory is not None:
            self.last_job_report = None
        self.state = state
        self.directory.setText(state.active_directory or "Nessuna cartella selezionata — TXT, Markdown e PDF")
        if state.warning:
            self.status.setText(f"{state.warning} — riprova Sync o scegli una cartella disponibile.")
        elif state.last_sync_outcome == "no_changes":
            self.status.setText("Indice aggiornato")
        elif state.search_available:
            self.status.setText("Indice disponibile")
        else:
            self.status.setText("Ricerca disponibile dopo l'indicizzazione")
        if self.closing:
            self.status.setText("Chiusura: attendo operazioni e letture in corso…")
        self.refresh_controls()

    def tick(self):
        pending, self.pending = self.pending, []
        for future, success, failure in pending:
            if not future.done():
                self.pending.append((future, success, failure))
                continue
            try:
                value = future.result()
            except Exception as exc:
                failure(exc)
            else:
                success(value)
        if self.closing or self.session is None or self.control_pending or self.poll_pending:
            return
        self.poll_pending = True

        def poll():
            state = self.session.status.execute()
            job = self.session.job_status.execute(state.job.job_id) if state.job else None
            return state, job

        def received(value):
            self.poll_pending = False
            if not self.closing and not self.control_pending:
                self.apply_state(value[0])
                self.apply_job(value[1])

        def failed(exc):
            self.poll_pending = False
            if not self.closing:
                self.error(exc)

        self.watch(self.coordinator.submit(poll), received, failed)

    def apply_job(self, job):
        if job and job.report is not None:
            self.last_job_report = job.report
            self.job_details.setEnabled(True)
        running = job and job.state in (JobState.PENDING, JobState.RUNNING)
        self.progress.setVisible(bool(job))
        if running:
            self.check_timer.stop()
            self.spinner_frame = (self.spinner_frame + 1) % 4
            self.sync.setText(f"{'◐◓◑◒'[self.spinner_frame]} Sync in corso")
            self.progress.setRange(0, 0 if job.progress is None else 100)
            if job.progress is not None:
                self.progress.setValue(int(job.progress * 100))
            phases = {"SCANNING": "Scansione", "EXTRACTING": "Estrazione", "ANALYZING": "Analisi",
                      "BUILDING": "Costruzione indice", "COMMITTING": "Salvataggio"}
            text = f"{phases[job.phase.value]} · {job.files_completed} / {job.files_total if job.files_total is not None else '?'} file"
            if job.current_file:
                text += f" · {job.current_file}"
            if self.state.search_available:
                text += " — Aggiornamento in corso: i risultati potrebbero non riflettere le modifiche più recenti"
            if not (self.state and self.state.warning):
                self.status.setText(text)
        elif job and job.job_id not in self.seen_terminal:
            self.seen_terminal.add(job.job_id)
            self.progress.setRange(0, 100)
            if job.state == JobState.COMPLETED:
                self.progress.setValue(100)
                self.sync.setText("✓ Aggiornato")
                self.check_timer.start()
            else:
                self.check_timer.stop()
                self.progress.setValue(0)
                self.sync.setText("Errore — riprova Sync")
                self.message.setText(job.error or "Sincronizzazione fallita")

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Scegli la directory dei documenti")
        if directory:
            self.invalidate()
            self.message.clear()
            self.control(lambda: self.session.select_directory.execute(directory), self.apply_state)

    def request_sync(self):
        self.message.clear()
        self.check_timer.stop()
        def requested(ref):
            self.apply_state(replace(self.state, job=ref))
        self.control(lambda: self.session.request_synchronization.execute(), requested)

    def search(self, offset=0):
        if not self.query.isEnabled():
            return
        self.generation += 1
        generation = self.generation
        self.detail_generation += 1
        self.preview.clear()
        self.results.setCurrentItem(None)
        self.message.clear()
        previous_snapshot = self.response.snapshot_id if self.response else None
        try:
            request = SearchRequest(self.query.text(), SearchField(self.field.currentData()), 50, offset)
            future = self.session.search.submit(request)
        except Exception as exc:
            self.error(exc)
            return

        def received(response):
            if generation != self.generation or self.closing:
                return
            if offset and response.snapshot_id != previous_snapshot:
                self.search(0)
                return
            self.response, self.offset = response, offset
            self.results.clear()
            for result in response.results:
                item = QTreeWidgetItem([result.filename, result.relative_path.value, result.format.value])
                item.setData(0, Qt.ItemDataRole.UserRole, result)
                self.results.addTopLevelItem(item)
            self.count.setText(f"{response.total_matches} risultati · pagina {offset // 50 + 1}")
            self.refresh_controls()

        self.watch(future, received, lambda exc: self.error(exc) if generation == self.generation and not self.closing else None)

    def show_document(self, item, _previous):
        self.detail_generation += 1
        generation = self.detail_generation
        self.preview.clear()
        self.refresh_controls()
        if item is None or self.response is None:
            return
        result = item.data(0, Qt.ItemDataRole.UserRole)
        try:
            future = self.session.get_document.submit(result.document_id, self.response.snapshot_id)
        except Exception as exc:
            self.error(exc)
            return
        self.watch(future,
                   lambda details: self.preview.setPlainText(details.extracted_text)
                   if generation == self.detail_generation and not self.closing else None,
                   lambda exc: self.error(exc) if generation == self.detail_generation and not self.closing else None)

    def open_selected(self):
        item = self.results.currentItem()
        if item is not None:
            result = item.data(0, Qt.ItemDataRole.UserRole)
            try:
                self.opener(self.state.active_directory, result.relative_path)
            except OSError as exc:
                self.error(exc)

    def clear_data(self):
        if QMessageBox.question(self, "Elimina dati locali",
                                "Eliminare indice, testo estratto e impostazioni locali? I documenti originali restano intatti.",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        self.invalidate()
        def cleared(state):
            self.check_timer.stop()
            self.sync.setText("Sync")
            self.progress.hide()
            self.message.clear()
            self.apply_state(state)
        self.control(self.session.clear_local_data.execute, cleared)

    def closeEvent(self, event):
        if self.closed:
            event.accept()
            return
        event.ignore()
        if self.closing:
            return
        self.closing = True
        self.invalidate()
        self.status.setText("Chiusura: attendo operazioni e letture in corso…")
        self.refresh_controls()

        # La composizione eventualmente in corso deve consegnare la sessione prima della chiusura.
        def begin_close():
            if self.control_pending:
                QTimer.singleShot(50, begin_close)
                return
            self.watch(self.coordinator.submit(lambda: self.session.close() if self.session else None), finished, failed)

        def finished(_):
            self.coordinator.shutdown(wait=False)
            self.timer.stop()
            self.check_timer.stop()
            self.closed = True
            self.close()

        def failed(exc):
            self.closing = False
            self.error(exc)
            self.refresh_controls()

        begin_close()
