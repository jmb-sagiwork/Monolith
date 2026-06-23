from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from monolith.adapters.terminal_adapter import TERMINAL_KEYS
from monolith.core.controller import MonolithController
from monolith.core.models import ACTION_TYPES, HandshakeRecipe, TargetWindow


class MonolithApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Monolith V2 - Formal Handshake Builder")
        self.root.geometry("1000x720")
        self.root.minsize(900, 640)
        self.window_values: list[TargetWindow] = []
        self.selected_step_index = -1
        self._build_ui()
        self.controller = MonolithController(
            self.root,
            {
                "log": self.append_log,
                "state": self.update_state,
                "captured": self.update_captured,
                "windows": self.update_windows,
                "website_status": self.update_website_status,
                "terminal_detection": self.update_terminal_detection,
                "terminal_preview": self.update_terminal_preview,
                "exported": self.report_exported,
                "full_passed": self.full_passed,
                "full_issues": self.full_issues,
            },
        )

    def run(self) -> None:
        self.controller.start()
        self.root.mainloop()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)
        ttk.Label(self.root, text="Monolith V2 - Formal Handshake Builder", font=("Segoe UI", 15, "bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=8
        )
        self._build_target_type()
        self._build_setup_panel()
        self._build_step_builder()
        self._build_result_and_logs()
        self._build_export_bar()
        self._show_setup("Terminal Emulator")

    def _build_target_type(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Target Type")
        frame.grid(row=1, column=0, sticky="ew", padx=12, pady=6)
        self.target_type_var = tk.StringVar(value="Terminal Emulator")
        for index, target_type in enumerate(["Terminal Emulator", "Website", "Desktop Application"]):
            ttk.Radiobutton(
                frame,
                text=target_type,
                value=target_type,
                variable=self.target_type_var,
                command=self._target_type_changed,
            ).grid(row=0, column=index, sticky="w", padx=12, pady=6)

    def _build_setup_panel(self) -> None:
        self.setup = ttk.LabelFrame(self.root, text="Target Setup Panel")
        self.setup.grid(row=2, column=0, sticky="ew", padx=12, pady=6)
        self.setup.columnconfigure(0, weight=1)
        self.terminal_frame = self._terminal_panel(self.setup)
        self.website_frame = self._website_panel(self.setup)
        self.desktop_frame = self._desktop_panel(self.setup)

    def _terminal_panel(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent)
        for col in range(5):
            frame.columnconfigure(col, weight=1 if col == 4 else 0)
        ttk.Button(frame, text="Detect Adapter", command=lambda: self.controller.detect_terminal_adapter()).grid(row=0, column=0, padx=6, pady=4)
        ttk.Button(frame, text="Refresh Windows", command=lambda: self.controller.refresh_desktop_windows()).grid(row=0, column=1, padx=6, pady=4)
        ttk.Button(frame, text="Select Session File", command=self._select_session_file).grid(row=0, column=2, padx=6, pady=4)
        ttk.Button(frame, text="Read Screen Preview", command=lambda: self.controller.read_terminal_preview()).grid(row=0, column=3, padx=6, pady=4)
        ttk.Label(frame, text="Detected Window:").grid(row=1, column=0, sticky="w", padx=6)
        self.terminal_window_var = tk.StringVar(value="None")
        ttk.Label(frame, textvariable=self.terminal_window_var).grid(row=1, column=1, columnspan=4, sticky="w", padx=6)
        ttk.Label(frame, text="Detected Session File:").grid(row=2, column=0, sticky="w", padx=6)
        self.session_file_var = tk.StringVar(value="None")
        ttk.Label(frame, textvariable=self.session_file_var).grid(row=2, column=1, columnspan=4, sticky="w", padx=6)
        ttk.Label(frame, text="Detected Adapter:").grid(row=3, column=0, sticky="w", padx=6)
        self.terminal_adapter_var = tk.StringVar(value="Manual row/column guidance")
        ttk.Label(frame, textvariable=self.terminal_adapter_var).grid(row=3, column=1, sticky="w", padx=6)
        ttk.Label(frame, text="Adapter Confidence:").grid(row=3, column=2, sticky="w", padx=6)
        self.terminal_confidence_var = tk.StringVar(value="low")
        ttk.Label(frame, textvariable=self.terminal_confidence_var).grid(row=3, column=3, sticky="w", padx=6)
        ttk.Label(frame, text="Terminal Action:").grid(row=4, column=0, sticky="w", padx=6, pady=(8, 2))
        self.terminal_action_var = tk.StringVar(value="Enter")
        ttk.Combobox(frame, textvariable=self.terminal_action_var, values=TERMINAL_KEYS, state="readonly", width=16).grid(row=4, column=1, sticky="w", padx=6, pady=(8, 2))
        ttk.Label(frame, text="Row:").grid(row=4, column=2, sticky="e", padx=6, pady=(8, 2))
        self.row_var = tk.StringVar(value="1")
        ttk.Entry(frame, textvariable=self.row_var, width=8).grid(row=4, column=3, sticky="w", padx=6, pady=(8, 2))
        ttk.Label(frame, text="Column:").grid(row=4, column=4, sticky="w", padx=6, pady=(8, 2))
        self.column_var = tk.StringVar(value="1")
        ttk.Entry(frame, textvariable=self.column_var, width=8).grid(row=4, column=4, sticky="e", padx=60, pady=(8, 2))
        ttk.Label(frame, text="Length:").grid(row=5, column=2, sticky="e", padx=6)
        self.length_var = tk.StringVar(value="10")
        ttk.Entry(frame, textvariable=self.length_var, width=8).grid(row=5, column=3, sticky="w", padx=6)
        ttk.Button(frame, text="Save Terminal Target", command=self._capture_terminal).grid(row=5, column=0, columnspan=2, sticky="w", padx=6, pady=4)
        self.preview_text = tk.Text(frame, height=4, wrap="none")
        self.preview_text.grid(row=6, column=0, columnspan=5, sticky="ew", padx=6, pady=6)
        return frame

    def _website_panel(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="URL:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.url_var = tk.StringVar(value="https://example.com")
        ttk.Entry(frame, textvariable=self.url_var).grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(frame, text="Open Browser", command=lambda: self.controller.open_website(self.url_var.get())).grid(row=0, column=2, padx=6, pady=4)
        ttk.Button(frame, text="Start Catch Mode", command=lambda: self.controller.start_website_catch()).grid(row=0, column=3, padx=6, pady=4)
        ttk.Button(frame, text="Stop Catch Mode", command=lambda: self.controller.stop_website_catch()).grid(row=0, column=4, padx=6, pady=4)
        ttk.Label(frame, text="Browser Status:").grid(row=1, column=0, sticky="w", padx=6)
        self.browser_status_var = tk.StringVar(value="Closed")
        ttk.Label(frame, textvariable=self.browser_status_var).grid(row=1, column=1, sticky="w", padx=6)
        ttk.Label(frame, text="Current URL:").grid(row=2, column=0, sticky="w", padx=6)
        self.current_url_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.current_url_var).grid(row=2, column=1, columnspan=4, sticky="w", padx=6)
        return frame

    def _desktop_panel(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)
        ttk.Button(frame, text="Refresh Windows", command=lambda: self.controller.refresh_desktop_windows()).grid(row=0, column=0, padx=6, pady=4)
        self.window_combo = ttk.Combobox(frame, state="readonly")
        self.window_combo.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        self.window_combo.bind("<<ComboboxSelected>>", self._window_selected)
        ttk.Button(frame, text="Select Window", command=self._window_selected).grid(row=0, column=2, padx=6, pady=4)
        ttk.Button(frame, text="Catch Target with F9", command=lambda: self.controller.catch_desktop_target()).grid(row=0, column=3, padx=6, pady=4)
        ttk.Label(frame, text="Selected Window:").grid(row=1, column=0, sticky="w", padx=6)
        self.desktop_window_var = tk.StringVar(value="None")
        ttk.Label(frame, textvariable=self.desktop_window_var).grid(row=1, column=1, columnspan=3, sticky="w", padx=6)
        ttk.Label(frame, text="Selected Process:").grid(row=2, column=0, sticky="w", padx=6)
        self.desktop_process_var = tk.StringVar(value="None")
        ttk.Label(frame, textvariable=self.desktop_process_var).grid(row=2, column=1, columnspan=3, sticky="w", padx=6)
        return frame

    def _build_step_builder(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Step Builder")
        frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=6)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        controls = ttk.Frame(frame)
        controls.grid(row=0, column=0, sticky="ew", padx=6, pady=4)
        ttk.Label(controls, text="Action Type:").grid(row=0, column=0, padx=4)
        self.action_var = tk.StringVar(value="Click")
        ttk.Combobox(controls, textvariable=self.action_var, values=ACTION_TYPES, state="readonly", width=16).grid(row=0, column=1, padx=4)
        ttk.Label(controls, text="Sample Input:").grid(row=0, column=2, padx=4)
        self.sample_input_var = tk.StringVar(value="ABC123")
        ttk.Entry(controls, textvariable=self.sample_input_var, width=24).grid(row=0, column=3, padx=4)
        ttk.Button(controls, text="Catch Target", command=self._catch_target).grid(row=0, column=4, padx=4)
        ttk.Button(controls, text="Test Selected Step", command=self._test_selected_step).grid(row=0, column=5, padx=4)
        ttk.Button(controls, text="Add Step", command=self._add_step).grid(row=0, column=6, padx=4)
        self.step_tree = ttk.Treeview(frame, columns=("action", "target", "status"), show="headings", height=8)
        for name, width in (("action", 130), ("target", 520), ("status", 160)):
            self.step_tree.heading(name, text=name.title())
            self.step_tree.column(name, width=width)
        self.step_tree.grid(row=1, column=0, sticky="nsew", padx=6, pady=4)
        self.step_tree.bind("<<TreeviewSelect>>", self._step_selected)
        step_buttons = ttk.Frame(frame)
        step_buttons.grid(row=2, column=0, sticky="ew", padx=6, pady=4)
        ttk.Button(step_buttons, text="Move Up", command=self._move_up).grid(row=0, column=0, padx=4)
        ttk.Button(step_buttons, text="Move Down", command=self._move_down).grid(row=0, column=1, padx=4)
        ttk.Button(step_buttons, text="Delete Step", command=self._delete_step).grid(row=0, column=2, padx=4)
        ttk.Button(step_buttons, text="Test Full Handshake", command=lambda: self.controller.test_full_handshake()).grid(row=0, column=3, padx=4)

    def _build_result_and_logs(self) -> None:
        lower = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        lower.grid(row=4, column=0, sticky="nsew", padx=12, pady=6)
        self.root.rowconfigure(4, weight=1)
        result = ttk.LabelFrame(lower, text="Result / Status")
        result.columnconfigure(1, weight=1)
        lower.add(result, weight=1)
        self.status_vars = {}
        for row, label in enumerate(["Target Type", "Adapter", "Current Step Status", "Full Handshake Status", "Captured Target"]):
            ttk.Label(result, text=f"{label}:").grid(row=row, column=0, sticky="w", padx=6, pady=3)
            var = tk.StringVar(value="Pending")
            ttk.Label(result, textvariable=var, wraplength=360).grid(row=row, column=1, sticky="w", padx=6, pady=3)
            self.status_vars[label] = var
        logs = ttk.LabelFrame(lower, text="Logs")
        logs.columnconfigure(0, weight=1)
        logs.rowconfigure(0, weight=1)
        lower.add(logs, weight=2)
        self.log_text = tk.Text(logs, height=8, wrap="word", state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=6)
        scroll = ttk.Scrollbar(logs, command=self.log_text.yview)
        scroll.grid(row=0, column=1, sticky="ns", padx=(0, 6), pady=6)
        self.log_text.configure(yscrollcommand=scroll.set)

    def _build_export_bar(self) -> None:
        frame = ttk.Frame(self.root)
        frame.grid(row=5, column=0, sticky="ew", padx=12, pady=8)
        ttk.Button(frame, text="Export JSON", command=lambda: self.controller.export_outputs()).grid(row=0, column=0, padx=4)
        ttk.Button(frame, text="Export Markdown", command=lambda: self.controller.export_outputs()).grid(row=0, column=1, padx=4)
        ttk.Button(frame, text="Generate Python Code", command=lambda: self.controller.export_outputs()).grid(row=0, column=2, padx=4)

    def _target_type_changed(self) -> None:
        target_type = self.target_type_var.get()
        self._show_setup(target_type)
        self.controller.set_target_type(target_type)

    def _show_setup(self, target_type: str) -> None:
        for frame in (self.terminal_frame, self.website_frame, self.desktop_frame):
            frame.grid_forget()
        selected = {
            "Terminal Emulator": self.terminal_frame,
            "Website": self.website_frame,
            "Desktop Application": self.desktop_frame,
        }[target_type]
        selected.grid(row=0, column=0, sticky="ew")

    def _select_session_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Session/Profile Files", "*.rsf *.ws *.edp *.rd3x *.rd5x"), ("All Files", "*.*")])
        if path:
            self.session_file_var.set(path)
            self.controller.select_session_file(path)

    def _capture_terminal(self) -> None:
        action = self.action_var.get()
        row = self.row_var.get().strip()
        column = self.column_var.get().strip()
        length = self.length_var.get().strip()
        terminal_action = self.terminal_action_var.get()
        if action == "Click":
            description = f"Terminal action: {terminal_action}"
        elif action == "Type":
            if not row or not column:
                messagebox.showwarning("Missing Terminal Position", "Enter a row and column before saving a Type target.")
                return
            description = f"Input at row {row}, column {column}"
        else:
            if not row or not column or not length:
                messagebox.showwarning("Missing Terminal Region", "Enter row, column, and length before saving an Extract Text target.")
                return
            description = f"Extract row {row}, column {column}, length {length}"
        metadata = {
            "description": description,
            "row": row,
            "column": column,
            "length": length,
            "session_file": self.session_file_var.get() if self.session_file_var.get() != "None" else "",
        }
        if action == "Click":
            metadata["terminal_action"] = terminal_action
        self.controller.catch_terminal_target(action, metadata)

    def _catch_target(self) -> None:
        target_type = self.target_type_var.get()
        if target_type == "Website":
            self.controller.start_website_catch()
        elif target_type == "Desktop Application":
            self.controller.catch_desktop_target()
        else:
            self._capture_terminal()

    def _add_step(self) -> None:
        sample = self.sample_input_var.get() if self.action_var.get() == "Type" else ""
        self.controller.add_step(self.action_var.get(), sample)

    def _test_selected_step(self) -> None:
        self.controller.test_selected_step(self.selected_step_index)

    def _step_selected(self, _event=None) -> None:
        selection = self.step_tree.selection()
        if selection:
            self.selected_step_index = self.step_tree.index(selection[0])
            values = self.step_tree.item(selection[0], "values")
            self.status_vars["Current Step Status"].set(values[2] if len(values) >= 3 else "Pending")

    def _move_up(self) -> None:
        self.selected_step_index = self.controller.move_step_up(self.selected_step_index)

    def _move_down(self) -> None:
        self.selected_step_index = self.controller.move_step_down(self.selected_step_index)

    def _delete_step(self) -> None:
        self.controller.delete_step(self.selected_step_index)
        self.selected_step_index = -1

    def _window_selected(self, _event=None) -> None:
        self.controller.select_window(self.window_combo.current())

    def append_log(self, line: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def update_state(self, recipe: HandshakeRecipe) -> None:
        self.status_vars["Target Type"].set(recipe.target_type or self.target_type_var.get())
        self.status_vars["Adapter"].set(recipe.adapter or "Unknown")
        self.status_vars["Full Handshake Status"].set(recipe.status)
        self.step_tree.delete(*self.step_tree.get_children())
        for step in recipe.steps:
            target = step.captured_target.label() if step.captured_target else "Not captured"
            self.step_tree.insert("", "end", values=(step.action, target, step.status))
        if 0 <= self.selected_step_index < len(recipe.steps):
            child = self.step_tree.get_children()[self.selected_step_index]
            self.step_tree.selection_set(child)
            self.step_tree.focus(child)

    def update_captured(self, target) -> None:
        self.status_vars["Captured Target"].set(target.label())

    def update_windows(self, windows: list[TargetWindow]) -> None:
        self.window_values = windows
        labels = [window.label() for window in windows]
        self.window_combo.configure(values=labels)
        if labels:
            self.window_combo.current(0)
            selected = windows[0]
            self.desktop_window_var.set(selected.title)
            self.desktop_process_var.set(selected.process_name or "Unknown")
            self.terminal_window_var.set(selected.label())

    def update_website_status(self, payload: dict) -> None:
        self.browser_status_var.set(payload.get("status", "Unknown"))
        self.current_url_var.set(payload.get("url", ""))

    def update_terminal_detection(self, payload: dict) -> None:
        detection = payload.get("detection", {})
        self.terminal_adapter_var.set(detection.get("adapter", "Manual row/column guidance"))
        self.terminal_confidence_var.set(detection.get("confidence", "low"))

    def update_terminal_preview(self, text: str) -> None:
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", text)

    def report_exported(self, path: str) -> None:
        messagebox.showinfo("Export Complete", f"Handshake files saved to:\n{path}")

    def full_passed(self, payload: dict) -> None:
        messagebox.showinfo(
            "Handshake Passed",
            f"Target Type: {payload.get('target_type')}\nSteps: {payload.get('steps')}\nBest Adapter: {payload.get('adapter')}",
        )

    def full_issues(self, payload: dict) -> None:
        messagebox.showwarning(
            "Handshake Completed With Issues",
            f"Passed: {payload.get('passed')}\nFailed: {payload.get('failed')}\nNeeds Manual Review: {payload.get('review')}\n\nYou can still export the recipe and developer code.",
        )
