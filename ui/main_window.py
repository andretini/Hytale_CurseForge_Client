import json
import os
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QFileDialog, QInputDialog
from api import ModClient
from ui.workers import InitWorker
from ui.layouts.sidebar import Sidebar
from ui.pages.search_page import SearchPage
from ui.pages.installed_page import InstalledPage
from ui.theme_manager import ThemeManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_key = ""
        self.game_path = ""
        self.config_file = "settings.json"

        self.setWindowTitle("Hytale Mod Manager")
        self.resize(1100, 750)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.client = ModClient(self.api_key)

        self.sidebar = Sidebar(
            on_navigate=self.switch_tab,
            on_set_folder=self.select_folder,
            on_theme_change=self.change_theme,
            on_set_api_key=self.set_api_key
        )
        self.stack = QStackedWidget()
        self.search_page = SearchPage(self.client)
        self.installed_page = InstalledPage(self.client)

        layout.addWidget(self.sidebar)
        self.stack.addWidget(self.search_page)
        self.stack.addWidget(self.installed_page)
        layout.addWidget(self.stack)

        self.load_settings()

        self.init_worker = InitWorker(self.client)
        self.init_worker.finished.connect(lambda msg: print(f"API: {msg}"))
        self.init_worker.start()

    def set_api_key(self):
        text, ok = QInputDialog.getText(self, "Set API Key", "Enter your CurseForge API Key:")
        if ok and text:
            self.api_key = text
            self.save_settings()
            self._reinitialize_client()

    def _reinitialize_client(self):
        """Creates a new API client and updates relevant components."""
        self.client = ModClient(self.api_key)

        if hasattr(self, 'search_page'):
            self.search_page.update_client(self.client)

        if hasattr(self, 'installed_page'):
            self.installed_page.update_client(self.client)

        self.init_worker = InitWorker(self.client)
        self.init_worker.finished.connect(lambda msg: print(f"API: {msg}"))
        self.init_worker.start()
        print("API Key set and client re-initialized.")

    def change_theme(self, theme_name):
        ThemeManager.apply_theme(theme_name)
        self.save_settings()

    def switch_tab(self, index, category=None):
        self.stack.setCurrentIndex(index)

        if index == 0 and category is not None:
            if hasattr(self, 'search_page'):
                self.search_page.set_category(category)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(None, "Select Game Folder")
        if folder:
            self.game_path = os.path.normpath(os.path.abspath(folder))
            self.save_settings()
            self.update_path_in_pages()

    def update_path_in_pages(self):
        self.sidebar.set_path_status(self.game_path)

        if hasattr(self, 'search_page'):
            self.search_page.set_game_path(self.game_path)
            print(f"DEBUG: Path sent to SearchPage: {self.game_path}")

        if hasattr(self, 'installed_page'):
            self.installed_page.set_game_path(self.game_path)
            print(f"DEBUG: Path sent to InstalledPage: {self.game_path}")

    def load_settings(self):
        if not os.path.exists(self.config_file):
            ThemeManager.apply_theme("Dark")
            return

        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)

                raw_path = data.get("game_path", "")
                if raw_path:
                    self.game_path = os.path.normpath(os.path.abspath(raw_path))

                self.api_key = data.get("api_key", "")
                if self.api_key:
                    self.client.headers["x-api-key"] = self.api_key

                saved_theme = data.get("theme", "Dark")

                self.sidebar.theme_combo.blockSignals(True)
                self.sidebar.theme_combo.setCurrentText(saved_theme)
                self.sidebar.theme_combo.blockSignals(False)

                ThemeManager.apply_theme(saved_theme)

                if self.game_path:
                    self.update_path_in_pages()

        except Exception as e:
            print(f"Load Error: {e}")

        except Exception as e:
            print(f"Load Error: {e}")

    def save_settings(self):
        try:
            data = {
                "game_path": self.game_path,
                "theme": self.sidebar.theme_combo.currentText(),
                "api_key": self.api_key
            }
            with open(self.config_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Save Error: {e}")
