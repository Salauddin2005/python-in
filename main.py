"""
CampusMate - Student Productivity Manager
A desktop BCA project built with Python Tkinter and SQLite.
Run: python main.py
"""

import csv
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "campusmate.db"

BG = "#F3F6FB"
NAVY = "#172554"
BLUE = "#2563EB"
TEAL = "#0F766E"
WHITE = "#FFFFFF"
TEXT = "#1E293B"
MUTED = "#64748B"
GREEN = "#15803D"
RED = "#B91C1C"


class CampusMateDB:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'Medium',
                    status TEXT NOT NULL DEFAULT 'Pending',
                    created_at TEXT NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    class_date TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
                    UNIQUE(subject, class_date)
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

    def add_task(self, title, subject, due_date, priority):
        with self.conn:
            self.conn.execute(
                "INSERT INTO tasks(title, subject, due_date, priority, created_at) VALUES(?,?,?,?,?)",
                (title, subject, due_date, priority, datetime.now().isoformat(timespec="seconds"))
            )

    def tasks(self, filter_status="All"):
        if filter_status == "All":
            return self.conn.execute(
                "SELECT * FROM tasks ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, due_date"
            ).fetchall()
        return self.conn.execute(
            "SELECT * FROM tasks WHERE status=? ORDER BY due_date", (filter_status,)
        ).fetchall()

    def set_task_status(self, task_id, status):
        with self.conn:
            self.conn.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))

    def delete_task(self, task_id):
        with self.conn:
            self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))

    def add_attendance(self, subject, class_date, status):
        with self.conn:
            self.conn.execute(
                "INSERT INTO attendance(subject, class_date, status) VALUES(?,?,?) "
                "ON CONFLICT(subject, class_date) DO UPDATE SET status=excluded.status",
                (subject, class_date, status)
            )

    def attendance(self):
        return self.conn.execute(
            "SELECT * FROM attendance ORDER BY class_date DESC, subject"
        ).fetchall()

    def attendance_summary(self):
        row = self.conn.execute(
            "SELECT COUNT(*) AS total, SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present FROM attendance"
        ).fetchone()
        total = row["total"] or 0
        present = row["present"] or 0
        return total, present, (present / total * 100 if total else 0)

    def save_note(self, title, content, note_id=None):
        with self.conn:
            if note_id:
                self.conn.execute(
                    "UPDATE notes SET title=?, content=?, updated_at=? WHERE id=?",
                    (title, content, datetime.now().isoformat(timespec="seconds"), note_id)
                )
            else:
                self.conn.execute(
                    "INSERT INTO notes(title, content, updated_at) VALUES(?,?,?)",
                    (title, content, datetime.now().isoformat(timespec="seconds"))
                )

    def notes(self):
        return self.conn.execute("SELECT * FROM notes ORDER BY updated_at DESC").fetchall()

    def delete_note(self, note_id):
        with self.conn:
            self.conn.execute("DELETE FROM notes WHERE id=?", (note_id,))

    def counts(self):
        total = self.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        pending = self.conn.execute("SELECT COUNT(*) FROM tasks WHERE status='Pending'").fetchone()[0]
        done = self.conn.execute("SELECT COUNT(*) FROM tasks WHERE status='Completed'").fetchone()[0]
        return total, pending, done

    def close(self):
        self.conn.close()


class CampusMateApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.db = CampusMateDB()
        self.title("CampusMate | Student Productivity Manager")
        self.geometry("1120x720")
        self.minsize(960, 620)
        self.configure(bg=BG)
        self.selected_note_id = None
        self.setup_style()
        self.build_layout()
        self.refresh_all()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background=WHITE, foreground=TEXT, rowheight=30,
                        fieldbackground=WHITE, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#E8EEF8", foreground=NAVY,
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#DBEAFE")],
                  foreground=[("selected", NAVY)])
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 10), font=("Segoe UI", 10, "bold"))

    def build_layout(self):
        header = tk.Frame(self, bg=NAVY, height=86)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="◈  CAMPUSMATE", bg=NAVY, fg=WHITE,
                 font=("Segoe UI", 20, "bold")).pack(side="left", padx=28)
        tk.Label(header, text="Your study life, organised.", bg=NAVY, fg="#CBD5E1",
                 font=("Segoe UI", 11)).pack(side="left", padx=12, pady=(8, 0))
        self.today_label = tk.Label(header, text=date.today().strftime("%d %b %Y"),
                                    bg=NAVY, fg=WHITE, font=("Segoe UI", 10, "bold"))
        self.today_label.pack(side="right", padx=28)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=22, pady=18)

        self.dashboard_tab = tk.Frame(self.notebook, bg=BG)
        self.tasks_tab = tk.Frame(self.notebook, bg=BG)
        self.attendance_tab = tk.Frame(self.notebook, bg=BG)
        self.notes_tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.dashboard_tab, text="  Dashboard  ")
        self.notebook.add(self.tasks_tab, text="  My Tasks  ")
        self.notebook.add(self.attendance_tab, text="  Attendance  ")
        self.notebook.add(self.notes_tab, text="  Quick Notes  ")

        self.build_dashboard()
        self.build_tasks()
        self.build_attendance()
        self.build_notes()

        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=24, pady=(0, 10))
        tk.Label(footer, text="CAMPUSMATE  •  Python + Tkinter + SQLite",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(side="left")
        tk.Button(footer, text="Export Data", command=self.export_data,
                  bg=TEAL, fg=WHITE, activebackground="#115E59",
                  activeforeground=WHITE, relief="flat", padx=16, pady=7,
                  cursor="hand2", font=("Segoe UI", 9, "bold")).pack(side="right")

    def section_title(self, parent, title, subtitle):
        tk.Label(parent, text=title, bg=BG, fg=NAVY,
                 font=("Segoe UI", 19, "bold")).pack(anchor="w", pady=(8, 2))
        tk.Label(parent, text=subtitle, bg=BG, fg=MUTED,
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 14))

    def build_dashboard(self):
        frame = self.dashboard_tab
        self.section_title(frame, "Welcome to CampusMate 👋",
                            "A simple place to manage assignments, attendance and study notes.")
        cards = tk.Frame(frame, bg=BG)
        cards.pack(fill="x", pady=4)
        self.card_values = {}
        for key, title, color in [
            ("total", "TOTAL TASKS", BLUE),
            ("pending", "PENDING", "#D97706"),
            ("done", "COMPLETED", GREEN),
            ("attendance", "ATTENDANCE", TEAL),
        ]:
            card = tk.Frame(cards, bg=WHITE, highlightbackground="#E2E8F0",
                            highlightthickness=1, padx=18, pady=15)
            card.pack(side="left", fill="x", expand=True, padx=(0, 12))
            tk.Label(card, text=title, bg=WHITE, fg=MUTED,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
            value = tk.Label(card, text="0", bg=WHITE, fg=color,
                             font=("Segoe UI", 24, "bold"))
            value.pack(anchor="w", pady=(5, 0))
            self.card_values[key] = value

        lower = tk.Frame(frame, bg=BG)
        lower.pack(fill="both", expand=True, pady=(20, 0))
        left = tk.Frame(lower, bg=WHITE, highlightbackground="#E2E8F0",
                        highlightthickness=1, padx=16, pady=14)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        tk.Label(left, text="Upcoming / pending tasks", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        self.dashboard_tasks = tk.Listbox(left, height=9, bg=WHITE, fg=TEXT,
                                          relief="flat", font=("Segoe UI", 10),
                                          selectbackground="#DBEAFE")
        self.dashboard_tasks.pack(fill="both", expand=True)

        right = tk.Frame(lower, bg="#EAF2FF", padx=18, pady=18)
        right.pack(side="right", fill="y")
        tk.Label(right, text="STUDY SMART", bg="#EAF2FF", fg=BLUE,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(right, text="Small steps every day\ncreate big results.",
                 bg="#EAF2FF", fg=NAVY, font=("Segoe UI", 16, "bold"),
                 justify="left").pack(anchor="w", pady=(10, 18))
        tk.Button(right, text="+  Add a task", command=lambda: self.notebook.select(self.tasks_tab),
                  bg=BLUE, fg=WHITE, relief="flat", padx=16, pady=9,
                  cursor="hand2", font=("Segoe UI", 10, "bold")).pack(anchor="w")

    def build_tasks(self):
        frame = self.tasks_tab
        self.section_title(frame, "My Tasks", "Add assignments and track your progress.")
        form = tk.Frame(frame, bg=WHITE, padx=14, pady=12,
                        highlightbackground="#E2E8F0", highlightthickness=1)
        form.pack(fill="x", pady=(0, 14))
        self.task_title = tk.StringVar()
        self.task_subject = tk.StringVar()
        self.task_due = tk.StringVar(value=date.today().isoformat())
        self.task_priority = tk.StringVar(value="Medium")

        self.form_field(form, "Task / Assignment", self.task_title, 0, 0, 28)
        self.form_field(form, "Subject", self.task_subject, 0, 1, 18)
        self.form_field(form, "Due date (YYYY-MM-DD)", self.task_due, 0, 2, 15)
        tk.Label(form, text="Priority", bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=3, sticky="w", padx=7)
        ttk.Combobox(form, textvariable=self.task_priority, values=["Low", "Medium", "High"],
                     state="readonly", width=10).grid(row=1, column=3, padx=7, pady=(4, 0), sticky="w")
        tk.Button(form, text="Add Task", command=self.add_task,
                  bg=BLUE, fg=WHITE, relief="flat", padx=16, pady=7,
                  cursor="hand2", font=("Segoe UI", 9, "bold")).grid(row=1, column=4, padx=8)

        controls = tk.Frame(frame, bg=BG)
        controls.pack(fill="x", pady=(0, 8))
        self.task_filter = tk.StringVar(value="All")
        tk.Label(controls, text="Show:", bg=BG, fg=MUTED).pack(side="left")
        filter_box = ttk.Combobox(controls, textvariable=self.task_filter,
                                  values=["All", "Pending", "Completed"],
                                  state="readonly", width=12)
        filter_box.pack(side="left", padx=8)
        filter_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh_tasks())
        tk.Button(controls, text="Mark selected completed", command=self.complete_task,
                  bg=GREEN, fg=WHITE, relief="flat", padx=12, pady=6).pack(side="right", padx=4)
        tk.Button(controls, text="Delete selected", command=self.delete_task,
                  bg="#FEE2E2", fg=RED, relief="flat", padx=12, pady=6).pack(side="right", padx=4)

        self.task_tree = ttk.Treeview(frame, columns=("id", "title", "subject", "due", "priority", "status"),
                                      show="headings")
        for col, label, width in [
            ("id", "ID", 45), ("title", "TASK", 300), ("subject", "SUBJECT", 150),
            ("due", "DUE DATE", 130), ("priority", "PRIORITY", 100), ("status", "STATUS", 110)
        ]:
            self.task_tree.heading(col, text=label)
            self.task_tree.column(col, width=width, anchor="w" if col in ("title", "subject") else "center")
        self.task_tree.pack(fill="both", expand=True)

    def form_field(self, parent, label, variable, row, col, width):
        tk.Label(parent, text=label, bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).grid(row=row, column=col, sticky="w", padx=7)
        tk.Entry(parent, textvariable=variable, width=width, relief="solid",
                 bd=1, font=("Segoe UI", 10)).grid(row=row + 1, column=col, padx=7, pady=(4, 0), ipady=5)

    def add_task(self):
        title = self.task_title.get().strip()
        subject = self.task_subject.get().strip()
        due = self.task_due.get().strip()
        if not title or not subject:
            messagebox.showwarning("Missing details", "Please enter both task name and subject.")
            return
        try:
            datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Invalid date", "Enter the due date as YYYY-MM-DD.")
            return
        self.db.add_task(title, subject, due, self.task_priority.get())
        self.task_title.set("")
        self.task_subject.set("")
        self.refresh_all()

    def selected_task_id(self):
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showinfo("Select a task", "Please select a task from the table first.")
            return None
        return int(self.task_tree.item(selected[0], "values")[0])

    def complete_task(self):
        task_id = self.selected_task_id()
        if task_id is not None:
            self.db.set_task_status(task_id, "Completed")
            self.refresh_all()

    def delete_task(self):
        task_id = self.selected_task_id()
        if task_id is not None and messagebox.askyesno("Confirm delete", "Delete this task?"):
            self.db.delete_task(task_id)
            self.refresh_all()

    def build_attendance(self):
        frame = self.attendance_tab
        self.section_title(frame, "Attendance Register", "Record each class as Present or Absent.")
        form = tk.Frame(frame, bg=WHITE, padx=16, pady=14,
                        highlightbackground="#E2E8F0", highlightthickness=1)
        form.pack(fill="x", pady=(0, 14))
        self.att_subject = tk.StringVar()
        self.att_date = tk.StringVar(value=date.today().isoformat())
        self.att_status = tk.StringVar(value="Present")
        self.form_field(form, "Subject", self.att_subject, 0, 0, 28)
        self.form_field(form, "Class date (YYYY-MM-DD)", self.att_date, 0, 1, 20)
        tk.Label(form, text="Status", bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", padx=7)
        ttk.Combobox(form, textvariable=self.att_status, values=["Present", "Absent"],
                     state="readonly", width=12).grid(row=1, column=2, padx=7, pady=(4, 0), sticky="w")
        tk.Button(form, text="Save Attendance", command=self.add_attendance,
                  bg=TEAL, fg=WHITE, relief="flat", padx=16, pady=7).grid(row=1, column=3, padx=10)

        self.att_summary_label = tk.Label(frame, text="", bg=BG, fg=TEAL,
                                          font=("Segoe UI", 12, "bold"))
        self.att_summary_label.pack(anchor="w", pady=(0, 10))
        self.att_tree = ttk.Treeview(frame, columns=("subject", "date", "status"), show="headings")
        for col, label, width in [("subject", "SUBJECT", 300), ("date", "CLASS DATE", 180),
                                  ("status", "STATUS", 150)]:
            self.att_tree.heading(col, text=label)
            self.att_tree.column(col, width=width, anchor="center")
        self.att_tree.pack(fill="both", expand=True)

    def add_attendance(self):
        subject = self.att_subject.get().strip()
        class_date = self.att_date.get().strip()
        if not subject:
            messagebox.showwarning("Missing subject", "Please enter the subject name.")
            return
        try:
            datetime.strptime(class_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Invalid date", "Enter the class date as YYYY-MM-DD.")
            return
        self.db.add_attendance(subject, class_date, self.att_status.get())
        self.att_subject.set("")
        self.refresh_all()

    def build_notes(self):
        frame = self.notes_tab
        self.section_title(frame, "Quick Notes", "Save short study notes and revision points.")
        body = tk.Frame(frame, bg=BG)
        body.pack(fill="both", expand=True)
        left = tk.Frame(body, bg=WHITE, padx=12, pady=12,
                        highlightbackground="#E2E8F0", highlightthickness=1)
        left.pack(side="left", fill="y", padx=(0, 14))
        tk.Label(left, text="SAVED NOTES", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.notes_list = tk.Listbox(left, width=30, height=18, relief="flat",
                                     font=("Segoe UI", 10), selectbackground="#DBEAFE")
        self.notes_list.pack(fill="both", expand=True, pady=8)
        self.notes_list.bind("<<ListboxSelect>>", self.load_note)
        tk.Button(left, text="+ New note", command=self.new_note,
                  bg=BLUE, fg=WHITE, relief="flat", padx=12, pady=7).pack(fill="x")

        editor = tk.Frame(body, bg=WHITE, padx=16, pady=14,
                          highlightbackground="#E2E8F0", highlightthickness=1)
        editor.pack(side="left", fill="both", expand=True)
        tk.Label(editor, text="NOTE TITLE", bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.note_title = tk.StringVar()
        tk.Entry(editor, textvariable=self.note_title, font=("Segoe UI", 11),
                 relief="solid", bd=1).pack(fill="x", pady=(5, 12), ipady=6)
        tk.Label(editor, text="NOTE CONTENT", bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.note_content = tk.Text(editor, wrap="word", font=("Segoe UI", 10),
                                    relief="solid", bd=1, padx=8, pady=8)
        self.note_content.pack(fill="both", expand=True, pady=(5, 12))
        actions = tk.Frame(editor, bg=WHITE)
        actions.pack(fill="x")
        tk.Button(actions, text="Save note", command=self.save_note,
                  bg=TEAL, fg=WHITE, relief="flat", padx=15, pady=7).pack(side="left")
        tk.Button(actions, text="Delete note", command=self.delete_note,
                  bg="#FEE2E2", fg=RED, relief="flat", padx=15, pady=7).pack(side="left", padx=8)

    def new_note(self):
        self.selected_note_id = None
        self.note_title.set("")
        self.note_content.delete("1.0", "end")
        self.notes_list.selection_clear(0, "end")

    def load_note(self, _event=None):
        selection = self.notes_list.curselection()
        if not selection:
            return
        notes = self.db.notes()
        note = notes[selection[0]]
        self.selected_note_id = note["id"]
        self.note_title.set(note["title"])
        self.note_content.delete("1.0", "end")
        self.note_content.insert("1.0", note["content"])

    def save_note(self):
        title = self.note_title.get().strip()
        content = self.note_content.get("1.0", "end").strip()
        if not title or not content:
            messagebox.showwarning("Missing details", "Enter a note title and some content.")
            return
        self.db.save_note(title, content, self.selected_note_id)
        self.new_note()
        self.refresh_notes()
        messagebox.showinfo("Saved", "Your note has been saved.")

    def delete_note(self):
        if self.selected_note_id is None:
            messagebox.showinfo("Select a note", "Choose a saved note first.")
            return
        if messagebox.askyesno("Confirm delete", "Delete this note?"):
            self.db.delete_note(self.selected_note_id)
            self.new_note()
            self.refresh_notes()

    def refresh_tasks(self):
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        for row in self.db.tasks(self.task_filter.get()):
            self.task_tree.insert("", "end", values=(
                row["id"], row["title"], row["subject"], row["due_date"],
                row["priority"], row["status"]
            ))

    def refresh_attendance(self):
        for item in self.att_tree.get_children():
            self.att_tree.delete(item)
        for row in self.db.attendance():
            self.att_tree.insert("", "end", values=(row["subject"], row["class_date"], row["status"]))
        total, present, percent = self.db.attendance_summary()
        self.att_summary_label.config(
            text=f"Attendance: {present}/{total} classes present  •  Overall: {percent:.1f}%"
        )

    def refresh_notes(self):
        self.notes_list.delete(0, "end")
        for row in self.db.notes():
            self.notes_list.insert("end", row["title"])

    def refresh_dashboard(self):
        total, pending, done = self.db.counts()
        att_total, att_present, att_percent = self.db.attendance_summary()
        self.card_values["total"].config(text=str(total))
        self.card_values["pending"].config(text=str(pending))
        self.card_values["done"].config(text=str(done))
        self.card_values["attendance"].config(text=f"{att_percent:.0f}%")
        self.dashboard_tasks.delete(0, "end")
        for row in self.db.tasks("Pending")[:8]:
            self.dashboard_tasks.insert("end", f'• {row["title"]}  —  {row["due_date"]}')
        if pending == 0:
            self.dashboard_tasks.insert("end", "You are all caught up. Great work!")

    def refresh_all(self):
        self.refresh_tasks()
        self.refresh_attendance()
        self.refresh_notes()
        self.refresh_dashboard()

    def export_data(self):
        folder = filedialog.askdirectory(title="Choose a folder for exported CSV files")
        if not folder:
            return
        folder = Path(folder)
        exports = [
            ("tasks", "SELECT title, subject, due_date, priority, status FROM tasks"),
            ("attendance", "SELECT subject, class_date, status FROM attendance"),
            ("notes", "SELECT title, content, updated_at FROM notes"),
        ]
        try:
            for name, query in exports:
                rows = self.db.conn.execute(query).fetchall()
                path = folder / f"campusmate_{name}.csv"
                with path.open("w", newline="", encoding="utf-8-sig") as file:
                    writer = csv.writer(file)
                    if rows:
                        writer.writerow(rows[0].keys())
                        writer.writerows([tuple(row) for row in rows])
                    else:
                        writer.writerow([name])
            messagebox.showinfo("Export complete", f"CSV files exported to:\\n{folder}")
        except OSError as error:
            messagebox.showerror("Export error", str(error))

    def on_close(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = CampusMateApp()
    app.mainloop()
