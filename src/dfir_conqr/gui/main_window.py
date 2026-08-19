from __future__ import annotations

import getpass
import webbrowser
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from dfir_conqr import __version__
from dfir_conqr.core import collectors as _collectors  # noqa: F401  (registers collectors)
from dfir_conqr.core.collector_base import all_collectors
from dfir_conqr.core.manifest import build_manifest, write_manifest
from dfir_conqr.core.report import write_html_report, write_json_report


class TriageWorker(QThread):
    progress = Signal(str)
    step_done = Signal(int)
    finished_ok = Signal(list, Path)
    failed = Signal(str)

    def __init__(self, selected_names: list[str], output_dir: Path, case_id: str, examiner: str):
        super().__init__()
        self.selected_names = selected_names
        self.output_dir = output_dir
        self.case_id = case_id
        self.examiner = examiner

    def run(self) -> None:
        try:
            registry = all_collectors()
            self.output_dir.mkdir(parents=True, exist_ok=True)
            results = []
            for i, name in enumerate(self.selected_names, start=1):
                self.progress.emit(f"Running: {name} ...")
                collector = registry[name]()
                result = collector.run(self.output_dir)
                results.append(result.to_dict())
                self.progress.emit(f"  -> {name}: {result.status}")
                self.step_done.emit(i)

            all_artifacts = [a for r in results for a in r.get("artifact_files", [])]
            manifest = build_manifest(
                case_id=self.case_id or "UNSET-CASE-ID",
                examiner=self.examiner or getpass.getuser(),
                output_dir=self.output_dir,
                artifact_relpaths=all_artifacts,
                tool_version=__version__,
            )
            write_manifest(manifest, self.output_dir)

            case_meta = {"case_id": self.case_id or "UNSET-CASE-ID", "examiner": self.examiner or getpass.getuser()}
            write_json_report(results, case_meta, self.output_dir)
            html_path = write_html_report(results, case_meta, self.output_dir)

            self.progress.emit("Done.")
            self.finished_ok.emit(results, html_path)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"DFIR-CONQR v{__version__}")
        self.resize(780, 640)

        self.registry = all_collectors()
        self.checkboxes: dict[str, QCheckBox] = {}
        self.worker: TriageWorker | None = None

        root = QWidget()
        layout = QVBoxLayout(root)

        # Case metadata row
        case_row = QHBoxLayout()
        self.case_id_input = QLineEdit()
        self.case_id_input.setPlaceholderText("Case ID (e.g. IR-2026-001)")
        self.examiner_input = QLineEdit()
        self.examiner_input.setPlaceholderText("Examiner name")
        case_row.addWidget(QLabel("Case:"))
        case_row.addWidget(self.case_id_input)
        case_row.addWidget(QLabel("Examiner:"))
        case_row.addWidget(self.examiner_input)
        layout.addLayout(case_row)

        # Output dir row
        out_row = QHBoxLayout()
        self.output_dir_input = QLineEdit(str(Path.cwd() / "triage_output"))
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._pick_output_dir)
        out_row.addWidget(QLabel("Output dir:"))
        out_row.addWidget(self.output_dir_input)
        out_row.addWidget(browse_btn)
        layout.addLayout(out_row)

        # Collector checklist
        layout.addWidget(QLabel("Select collectors to run:"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        checklist_widget = QWidget()
        checklist_layout = QVBoxLayout(checklist_widget)
        for name, cls in sorted(self.registry.items()):
            cb = QCheckBox(f"{name}  -  {cls.description}")
            cb.setChecked(True)
            self.checkboxes[name] = cb
            checklist_layout.addWidget(cb)
        checklist_layout.addStretch()
        scroll.setWidget(checklist_widget)
        scroll.setMaximumHeight(220)
        layout.addWidget(scroll)

        # Select all / none
        sel_row = QHBoxLayout()
        all_btn = QPushButton("Select All")
        all_btn.clicked.connect(lambda: self._set_all(True))
        none_btn = QPushButton("Select None")
        none_btn.clicked.connect(lambda: self._set_all(False))
        sel_row.addWidget(all_btn)
        sel_row.addWidget(none_btn)
        sel_row.addStretch()
        layout.addLayout(sel_row)

        # Run button + progress
        self.run_btn = QPushButton("Start Triage Collection")
        self.run_btn.clicked.connect(self._start_run)
        layout.addWidget(self.run_btn)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        layout.addWidget(QLabel("Log:"))
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

        self.open_report_btn = QPushButton("Open HTML Report")
        self.open_report_btn.setEnabled(False)
        self.open_report_btn.clicked.connect(self._open_report)
        layout.addWidget(self.open_report_btn)

        self.setCentralWidget(root)
        self._report_path: Path | None = None

    def _set_all(self, checked: bool) -> None:
        for cb in self.checkboxes.values():
            cb.setChecked(checked)

    def _pick_output_dir(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Choose output directory")
        if chosen:
            self.output_dir_input.setText(chosen)

    def _start_run(self) -> None:
        selected = [name for name, cb in self.checkboxes.items() if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "No collectors selected", "Select at least one collector.")
            return

        self.run_btn.setEnabled(False)
        self.open_report_btn.setEnabled(False)
        self.log_view.clear()
        self.progress_bar.setMaximum(len(selected))
        self.progress_bar.setValue(0)

        self.worker = TriageWorker(
            selected_names=selected,
            output_dir=Path(self.output_dir_input.text()),
            case_id=self.case_id_input.text(),
            examiner=self.examiner_input.text(),
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.step_done.connect(self.progress_bar.setValue)
        self.worker.finished_ok.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_progress(self, msg: str) -> None:
        self.log_view.append(msg)

    def _on_finished(self, results: list, html_path: Path) -> None:
        self.run_btn.setEnabled(True)
        self._report_path = html_path
        self.open_report_btn.setEnabled(True)
        self.log_view.append(f"\nReport ready: {html_path}")

    def _on_failed(self, error: str) -> None:
        self.run_btn.setEnabled(True)
        QMessageBox.critical(self, "Collection failed", error)

    def _open_report(self) -> None:
        if self._report_path:
            webbrowser.open(self._report_path.as_uri())
