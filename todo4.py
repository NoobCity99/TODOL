import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QScrollArea, QCheckBox, QLabel,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt

DATA_FILE = "tasks.json"

# ===========================
# Main App Class
# ===========================


class ToDoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("To-Do List App")
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
            self.create_task_widget(task_text, False)
            self.task_input.clear()
            self.save_tasks()
        else:
            QMessageBox.warning(self, "Empty Task", "Please enter a task.")

    def create_task_widget(self, text, done):
        checkbox = QCheckBox(text)
        checkbox.setChecked(done)
        checkbox.stateChanged.connect(self.save_tasks)
        self.task_container.addWidget(checkbox)
        self.tasks.append(checkbox)

    def remove_completed(self):
        for task in self.tasks[:]:
            if task.isChecked():
                self.task_container.removeWidget(task)
                task.setParent(None)
                self.tasks.remove(task)
        self.save_tasks()

    def clear_tasks(self):
        reply = QMessageBox.question(self, "Clear All", "Delete all tasks?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            for task in self.tasks:
                self.task_container.removeWidget(task)
                task.setParent(None)
            self.tasks.clear()
            self.save_tasks()

    def save_tasks(self):
        data = [{"task": task.text(), "done": task.isChecked()}
                for task in self.tasks]
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load_tasks(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                for item in data:
                    self.create_task_widget(item["task"], item["done"])
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to load tasks:\n{e}")

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
