import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QScrollArea, QCheckBox, QLabel,
    QMessageBox, QFrame, QDialog, QDialogButtonBox,
    QDateTimeEdit, QSpinBox
)
from PyQt6.QtCore import Qt, QDateTime, QTimer
from PyQt6.QtGui import QIcon
DATA_FILE = "tasks.json"


class TaskCheckBox(QCheckBox):
    def __init__(self, text, done, parent=None, due=None, reminder_hours=None):
        super().__init__(text, parent)
        self.base_text = text
        self.due = due
        self.reminder_hours = reminder_hours
        self.reminder_timer = None
        self.setChecked(done)
        self.stateChanged.connect(parent.save_tasks)
        self.update_text()
        self.schedule_reminder()

    def update_text(self):
        text = self.base_text
        if self.due:
            text += f" (due: {self.due.toString('yyyy-MM-dd HH:mm')})"
        self.setText(text)

    def mouseDoubleClickEvent(self, event):
        app = self.parent()
        if hasattr(app, 'open_due_dialog'):
            due, reminder = app.open_due_dialog(self.due, self.reminder_hours)
            if due is not None:
                self.due = due
                self.reminder_hours = reminder
            else:
                self.due = None
                self.reminder_hours = None
            self.update_text()
            self.schedule_reminder()
            app.save_tasks()
        event.accept()

    def schedule_reminder(self):
        if self.reminder_timer:
            self.reminder_timer.stop()
            self.reminder_timer.deleteLater()
            self.reminder_timer = None
        if self.due and self.reminder_hours:
            msecs_until = QDateTime.currentDateTime().msecsTo(
                self.due) - self.reminder_hours * 3600 * 1000
            if msecs_until > 0:
                self.reminder_timer = QTimer(self)
                self.reminder_timer.setSingleShot(True)

                def notify():
                    QMessageBox.information(
                        self,
                        "Task Reminder",
                        f"'{self.base_text}' is due at {self.due.toString('yyyy-MM-dd HH:mm')}"
                    )
                self.reminder_timer.timeout.connect(notify)
                self.reminder_timer.start(msecs_until)


# ===========================
# Main App Class
# ===========================


class ToDoApp(QWidget):
    def __init__(self):
        super().__init__()
        icon_path = os.path.join(os.path.dirname(__file__), "icon toto.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("TODOL")
        self.setGeometry(300, 100, 400, 500)
        self.setStyleSheet(self.load_styles())

        self.tasks = []

        # Layout setup
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Task input
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter a new task...")
        main_layout.addWidget(self.task_input)

        add_button = QPushButton("Add Task")
        add_button.clicked.connect(self.add_task)
        main_layout.addWidget(add_button)

        # Scrollable area for tasks
        self.task_container = QVBoxLayout()
        self.task_container.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_widget = QWidget()
        scroll_widget.setLayout(self.task_container)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        # Control buttons
        control_layout = QHBoxLayout()
        remove_button = QPushButton("Remove Completed")
        remove_button.clicked.connect(self.remove_completed)

        clear_button = QPushButton("Clear All")
        clear_button.clicked.connect(self.clear_tasks)

        control_layout.addWidget(remove_button)
        control_layout.addWidget(clear_button)
        main_layout.addLayout(control_layout)

        # Load saved tasks
        self.load_tasks()

    def add_task(self):
        task_text = self.task_input.text().strip()
        if task_text:
            due, reminder = self.open_due_dialog()
            self.create_task_widget(task_text, False, due, reminder)
            self.task_input.clear()
            self.save_tasks()
        else:
            QMessageBox.warning(self, "Empty Task", "Please enter a task.")

    def create_task_widget(self, text, done, due=None, reminder=None):
        checkbox = TaskCheckBox(text, done, self, due, reminder)
        self.task_container.addWidget(checkbox)
        self.tasks.append(checkbox)

    def remove_completed(self):
        for task in self.tasks[:]:
            if task.isChecked():
                if task.reminder_timer:
                    task.reminder_timer.stop()
                self.task_container.removeWidget(task)
                task.setParent(None)
                self.tasks.remove(task)
        self.save_tasks()

    def clear_tasks(self):
        reply = QMessageBox.question(self, "Clear All", "Delete all tasks?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            for task in self.tasks:
                if task.reminder_timer:
                    task.reminder_timer.stop()
                self.task_container.removeWidget(task)
                task.setParent(None)
            self.tasks.clear()
            self.save_tasks()

    def save_tasks(self):
        data = [{
            "task": task.base_text,
            "done": task.isChecked(),
            "due": task.due.toString(Qt.DateFormat.ISODate) if task.due else None,
            "reminder": task.reminder_hours,
        } for task in self.tasks]
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load_tasks(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                for item in data:
                    due = QDateTime.fromString(
                        item.get("due"), Qt.DateFormat.ISODate) if item.get("due") else None
                    self.create_task_widget(
                        item["task"], item["done"], due, item.get("reminder"))
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to load tasks:\n{e}")

    def open_due_dialog(self, existing_due=None, existing_reminder=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Due Date")

        layout = QVBoxLayout(dialog)
        enable_box = QCheckBox("Enable Due Date")
        layout.addWidget(enable_box)

        due_edit = QDateTimeEdit()
        due_edit.setCalendarPopup(True)
        due_edit.setDateTime(existing_due or QDateTime.currentDateTime())
        layout.addWidget(due_edit)

        reminder_label = QLabel("Reminder (hours before):")
        reminder_spin = QSpinBox()
        reminder_spin.setRange(1, 24)
        reminder_spin.setValue(existing_reminder or 1)
        layout.addWidget(reminder_label)
        layout.addWidget(reminder_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        if existing_due:
            enable_box.setChecked(True)
        else:
            due_edit.setEnabled(False)
            reminder_label.setEnabled(False)
            reminder_spin.setEnabled(False)

        def toggle(state):
            due_edit.setEnabled(state)
            reminder_label.setEnabled(state)
            reminder_spin.setEnabled(state)

        enable_box.toggled.connect(toggle)

        if dialog.exec() == QDialog.DialogCode.Accepted and enable_box.isChecked():
            return due_edit.dateTime(), reminder_spin.value()
        return None, None

    def load_styles(self):
        return """
        QWidget {
            background-color: #1e1e2f;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 11pt;
        }
        QLineEdit {
            background-color: #2b2b3c;
            color: #ffffff;
            padding: 5px;
            border: 1px solid #444;
        }
        QPushButton {
            background-color: #3e3e50;
            color: #ffffff;
            padding: 6px;
            border: none;
        }
        QPushButton:hover {
            background-color: #5c5cff;
        }
        QCheckBox {
            background-color: #2f2f3f;
            padding: 5px;
        }
        QScrollArea {
            background-color: #1e1e2f;
            border: none;
        }
        """


# ===========================
# Run the App
# ===========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ToDoApp()
    window.show()
    sys.exit(app.exec())
