# CampusMate – Student Productivity Manager

**A desktop application built with Python, Tkinter and SQLite for BCA students.**

## Overview
CampusMate helps students organise everyday academic work in one place. It includes a dashboard, assignment/task manager, attendance register and quick study notes. Information is saved locally in an SQLite database.

## Features
- Dashboard showing total, pending and completed tasks.
- Add tasks with subject, due date and priority.
- Mark tasks as completed or delete them.
- Record daily subject-wise attendance.
- Calculate overall attendance percentage.
- Create, edit and delete quick study notes.
- Export tasks, attendance and notes to CSV files.
- Local SQLite database; no internet connection or third-party packages required.

## Technology used
- Python 3
- Tkinter – graphical user interface
- SQLite – local database
- CSV module – data export
- `datetime` and `pathlib` – date and file handling

## Requirements
- Python 3.8 or newer
- Tkinter (included with most standard Python installations)

No `pip install` is required.

## How to run
1. Download or clone this repository.
2. Open Command Prompt / Terminal in the project folder.
3. Run:

   ```bash
   python main.py
   ```

4. The CampusMate desktop window will open.
5. Add sample tasks, attendance records and notes to explore the application.

The file `campusmate.db` is created automatically in the project folder when the program runs.

## Project structure

```text
CampusMate/
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
└── docs/
    └── PROJECT_REPORT.md
```

## Database design
The application creates three SQLite tables:

| Table | Purpose |
|---|---|
| `tasks` | Stores task title, subject, due date, priority and status |
| `attendance` | Stores subject, class date and Present/Absent status |
| `notes` | Stores note title, content and last updated time |

## Basic testing checklist
- Add a task with a valid date.
- Try to add a task without a title; the app should show a validation message.
- Mark a task as completed.
- Add attendance for a subject and date.
- Add the same subject/date again with a different status; the existing record is updated.
- Save and reopen a note.
- Export CSV files and confirm that they contain the saved records.

## Limitations and future scope
This is a local single-user learning project. Future versions could include student login, cloud backup, reminders, charts and multi-user access.

## Academic note
Use sample information while demonstrating the application. Review the project with your internship mentor and adapt the documentation to match your actual requirements and tests.
