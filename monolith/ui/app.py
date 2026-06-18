from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from monolith.core.controller import MonolithController
from monolith.core.models import ScanResult, SessionProfile, TargetWindow


class MonolithApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Monolith - Legacy Emulator Handshake Tester")
        self.root.geometry("900x650")
        self.root.minsize(780, 560)
        self.window_values: list[TargetWindow] = []
        self.profile_values: list[SessionProfile] = []
        self._build_ui()
        self.controller = MonolithController(
            self.root,
            {
                "log": self.append_log,
                "windows": self.update_windows,
                "profiles": self.update_profiles,
                "result": self.update_result,
                "exported": self.report_exported,
            },
        )

    def run(self) -> None:
        self.controller.start()
        self.root.mainloop()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)
        pad = {"padx": 12, "pady": 8}

        header = ttk.Label(self.root, text="Monolith - Legacy Emulator Handshake Tester", font=("Segoe UI", 15, "bold"))
        header.grid(row=0, column=0, sticky="w", **pad)

        target = ttk.LabelFrame(self.root, text="Target")
        target.grid(row=1, column=0, sticky="ew", **pad)
        target.columnconfigure(1, weight=1)
        target.columnconfigure(3, weight=1)

        ttk.Button(target, text="Refresh Windows", command=self._refresh_windows).grid(row=0, column=0, sticky="w", padx=8, pady=8)
        ttk.Button(target, text="Select Session File", command=self._select_file).grid(row=0, column=1, sticky="w", padx=8, pady=8)
        ttk.Button(target, text="Start Scan", command=self._start_scan).grid(row=0, column=2, sticky="w", padx=8, pady=8)

        ttk.Label(target, text="Window:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.window_combo = ttk.Combobox(target, state="readonly")
        self.window_combo.grid(row=1, column=1, columnspan=3, sticky="ew", padx=8, pady=4)
        self.window_combo.bind("<<ComboboxSelected>>", self._window_selected)

        ttk.Label(target, text="File:").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.file_var = tk.StringVar(value="")
        ttk.Label(target, textvariable=self.file_var).grid(row=2, column=1, columnspan=3, sticky="w", padx=8, pady=4)

        result = ttk.LabelFrame(self.root, text="Detection Result")
        result.grid(row=2, column=0, sticky="ew", **pad)
        result.columnconfigure(1, weight=1)
        result.columnconfigure(3, weight=1)
        self.product_var = self._result_row(result, 0, "Product Guess:")
        self.launcher_var = self._result_row(result, 1, "Launcher Guess:")
        self.backend_var = self._result_row(result, 2, "Backend Guess:")
        self.adapter_var = self._result_row(result, 3, "Best Adapter:")
        self.selected_window_var = self._result_row(result, 4, "Selected Window:")
        self.selected_profile_var = self._result_row(result, 5, "Selected Profile:")

        lower = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        lower.grid(row=3, column=0, sticky="nsew", **pad)

        tests = ttk.LabelFrame(lower, text="Handshake Tests")
        tests.columnconfigure(1, weight=1)
        lower.add(tests, weight=1)
        ttk.Button(tests, text="Test UIA", command=self._test_uia).grid(row=0, column=0, padx=8, pady=8)
        ttk.Button(tests, text="Probe DLLs", command=self._probe_dlls).grid(row=0, column=1, sticky="w", padx=8, pady=8)
        ttk.Button(tests, text="Test Clipboard", command=self._test_clipboard).grid(row=0, column=2, padx=8, pady=8)
        ttk.Button(tests, text="Export Report", command=self._export_report).grid(row=0, column=3, padx=8, pady=8)
        ttk.Button(tests, text="OCR Snapshot", state="disabled").grid(row=0, column=4, padx=8, pady=8)

        self.adapter_tree = ttk.Treeview(tests, columns=("status", "confidence", "notes"), show="tree headings", height=5)
        self.adapter_tree.heading("#0", text="Adapter")
        self.adapter_tree.heading("status", text="Status")
        self.adapter_tree.heading("confidence", text="Confidence")
        self.adapter_tree.heading("notes", text="Notes")
        self.adapter_tree.column("#0", width=160, stretch=False)
        self.adapter_tree.column("status", width=100, stretch=False)
        self.adapter_tree.column("confidence", width=100, stretch=False)
        self.adapter_tree.column("notes", width=500)
        self.adapter_tree.grid(row=1, column=0, columnspan=5, sticky="nsew", padx=8, pady=4)
        tests.rowconfigure(1, weight=1)

        logs = ttk.LabelFrame(lower, text="Logs")
        logs.columnconfigure(0, weight=1)
        logs.rowconfigure(0, weight=1)
        lower.add(logs, weight=2)
        self.log_text = tk.Text(logs, height=10, wrap="word", state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        scroll = ttk.Scrollbar(logs, command=self.log_text.yview)
        scroll.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.log_text.configure(yscrollcommand=scroll.set)

    def _result_row(self, parent, row: int, label: str) -> tk.StringVar:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=3)
        var = tk.StringVar(value="Unknown")
        ttk.Label(parent, textvariable=var).grid(row=row, column=1, columnspan=3, sticky="w", padx=8, pady=3)
        return var

    def append_log(self, line: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def update_windows(self, windows: list[TargetWindow], selected: TargetWindow) -> None:
        self.window_values = windows
        labels = [window.label() for window in windows]
        self.window_combo.configure(values=labels)
        if labels:
            index = windows.index(selected) if selected in windows else 0
            self.window_combo.current(index)

    def update_profiles(self, profiles: list[SessionProfile], selected: SessionProfile) -> None:
        self.profile_values = profiles
        if selected.path:
            self.file_var.set(selected.path)

    def update_result(self, result: ScanResult) -> None:
        self.product_var.set(result.product_guess)
        self.launcher_var.set(result.launcher_guess)
        self.backend_var.set(result.backend_guess)
        self.adapter_var.set(result.best_adapter)
        self.selected_window_var.set(result.selected_window.label() if result.selected_window.title else "None")
        self.selected_profile_var.set(result.selected_profile.path or "None")
        self.file_var.set(result.selected_profile.path or "")
        self.adapter_tree.delete(*self.adapter_tree.get_children())
        for adapter in result.adapters:
            self.adapter_tree.insert("", "end", text=adapter.name, values=(adapter.status, adapter.confidence, adapter.notes))

    def report_exported(self, path: str) -> None:
        messagebox.showinfo("Report Exported", f"Report saved to:\n{path}")

    def _refresh_windows(self) -> None:
        self.controller.refresh_windows()

    def _select_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Session/Profile File",
            filetypes=[
                ("Session/Profile Files", "*.rsf *.ws *.edp *.rd3x *.rd5x"),
                ("All Files", "*.*"),
            ],
        )
        if path:
            self.controller.select_profile(path)

    def _window_selected(self, _event=None) -> None:
        self.controller.select_window_by_index(self.window_combo.current())

    def _start_scan(self) -> None:
        self.controller.start_scan()

    def _test_uia(self) -> None:
        self.controller.test_uia()

    def _probe_dlls(self) -> None:
        self.controller.probe_dlls()

    def _test_clipboard(self) -> None:
        if messagebox.askyesno("Test Clipboard", "This will focus the selected window and send a copy command only. Continue?"):
            self.controller.test_clipboard()

    def _export_report(self) -> None:
        self.controller.export_report()
