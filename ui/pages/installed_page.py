import json
import os
import shutil
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QMessageBox, QFrame
)
from PySide6.QtCore import Qt

from ui.common.maps import PATH_MAP
from ui.components.universal_card import UniversalCard
from ui.layouts.mod_dialog import ModDetailsDialog
from ui.workers import DownloadWorker, UpdateCheckWorker
from registry import ModRegistry


class InstalledPage(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.game_path = ""
        self.registry = ModRegistry("")
        self.available_updates = {}
        self._update_queue = []
        self.setup_ui()

    def update_client(self, client):
        self.client = client

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        title = QLabel("Installed Files")
        title.setObjectName("Title")
        layout.addWidget(title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        refresh_btn = QPushButton("Refresh List")
        refresh_btn.setFixedWidth(120)
        refresh_btn.clicked.connect(self.refresh)
        btn_row.addWidget(refresh_btn)

        self.check_btn = QPushButton("Check for Updates")
        self.check_btn.setFixedWidth(160)
        self.check_btn.setObjectName("ActionBtn")
        self.check_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.check_btn.clicked.connect(self.check_updates)
        btn_row.addWidget(self.check_btn)

        self.update_all_btn = QPushButton("Update All")
        self.update_all_btn.setFixedWidth(120)
        self.update_all_btn.setObjectName("ActionBtn")
        self.update_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_all_btn.clicked.connect(self.update_all)
        self.update_all_btn.setVisible(False)
        btn_row.addWidget(self.update_all_btn)

        self.status_label = QLabel("")
        self.status_label.setObjectName("DimLabel")
        btn_row.addWidget(self.status_label)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.viewport().setAutoFillBackground(False)

        self.content = QWidget()
        self.content.setObjectName("ScrollContent")
        self.content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.layout_content = QVBoxLayout(self.content)
        self.layout_content.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout_content.setSpacing(12)

        scroll.setWidget(self.content)
        layout.addWidget(scroll)

    def set_game_path(self, path):
        self.game_path = os.path.normpath(path) if path else ""
        self.registry = ModRegistry(self.game_path)
        self.available_updates = {}
        self.update_all_btn.setVisible(False)
        self.status_label.setText("")
        self.refresh()

    def check_updates(self):
        if not self.game_path:
            QMessageBox.warning(self, "Error", "Set game folder first!")
            return

        entries = self.registry.get_all()
        if not entries:
            self.status_label.setText("No registered mods to check.")
            return

        self.check_btn.setText("Checking...")
        self.check_btn.setEnabled(False)
        self.status_label.setText("")
        self.update_all_btn.setVisible(False)

        self.check_worker = UpdateCheckWorker(self.client, self.registry)
        self.check_worker.progress.connect(self._on_check_progress)
        self.check_worker.finished.connect(self._on_check_finished)
        self.check_worker.error.connect(self._on_check_error)
        self.check_worker.start()

    def _on_check_progress(self, current, total):
        self.status_label.setText(f"Checking {current}/{total}...")

    def _on_check_finished(self, result_json):
        self.check_btn.setText("Check for Updates")
        self.check_btn.setEnabled(True)

        self.available_updates = json.loads(result_json)
        count = len(self.available_updates)

        if count > 0:
            self.status_label.setText(f"{count} update(s) available")
            self.update_all_btn.setText(f"Update All ({count})")
            self.update_all_btn.setVisible(True)
        else:
            self.status_label.setText("All mods are up to date.")
            self.update_all_btn.setVisible(False)

        self.refresh()

    def _on_check_error(self, msg):
        self.check_btn.setText("Check for Updates")
        self.check_btn.setEnabled(True)
        self.status_label.setText(f"Error: {msg}")

    def refresh(self):
        self.clear_list()
        if not self.game_path or not os.path.exists(self.game_path):
            self.layout_content.addWidget(QLabel("Please set game folder."))
            return

        found_any = False

        for class_id, subfolder in PATH_MAP.items():
            folder_path = os.path.normpath(os.path.join(self.game_path, subfolder))
            if not os.path.exists(folder_path):
                continue

            try:
                items = os.listdir(folder_path)
                if not items:
                    continue

                found_any = True
                cat_label = QLabel(subfolder.upper())
                cat_label.setProperty("header", "true")
                self.layout_content.addWidget(cat_label)

                for name in items:
                    full_path = os.path.join(folder_path, name)
                    rel_path = os.path.join(subfolder, name)

                    is_dir = os.path.isdir(full_path)
                    is_file = name.endswith(('.jar', '.zip'))

                    if not (is_dir or is_file):
                        continue

                    created = datetime.fromtimestamp(os.path.getctime(full_path)).strftime('%Y-%m-%d')

                    if is_dir:
                        size_mb = self.get_dir_size(full_path)
                        icon = "🌍" if "Saves" in subfolder else "📂"
                    else:
                        size_mb = os.path.getsize(full_path) / (1024 * 1024)
                        icon = "📦"

                    mod_id_str, reg_entry = self.registry.find_by_filename(name)
                    has_update = mod_id_str is not None and mod_id_str in self.available_updates

                    fake_data = {
                        'name': reg_entry.get('mod_name', name) if reg_entry else name,
                        'authors': [{'name': 'Local File'}],
                        'summary': f"Location: {rel_path}",
                        'classId': class_id
                    }

                    card = UniversalCard(
                        title=fake_data['name'],
                        subtitle=f"{size_mb:.2f} MB  •  {created}",
                        is_installed=True,
                        has_update=has_update,
                        update_callback=(
                            lambda btn, mid=mod_id_str: self.update_single(mid, btn)
                        ) if has_update else None,
                        delete_callback=lambda p=rel_path, mid=mod_id_str: self.delete_file(p, mod_id=mid),
                        click_callback=lambda d=fake_data, p=rel_path, mid=mod_id_str: ModDetailsDialog(
                            d, is_installed=True,
                            remove_callback=lambda: self.delete_file(p, mod_id=mid),
                            parent=self
                        ).exec(),
                        icon_char=icon
                    )
                    self.layout_content.addWidget(card)
            except Exception as e:
                print(f"Error scanning {subfolder}: {e}")

        if not found_any:
            self.layout_content.addWidget(QLabel("No installed content found."))

    def update_single(self, mod_id_str, btn=None):
        mod_id = int(mod_id_str)
        reg_entry = self.registry.get(mod_id)
        if not reg_entry:
            return

        old_name = reg_entry.get('file_name', '')
        class_id = reg_entry.get('class_id')
        subfolder = PATH_MAP.get(class_id, "UserData/Mods")
        target_dir = os.path.normpath(os.path.join(self.game_path, subfolder))

        old_path = os.path.join(target_dir, old_name)
        if os.path.exists(old_path):
            if os.path.isdir(old_path):
                shutil.rmtree(old_path)
            else:
                os.remove(old_path)

        if btn and hasattr(btn, "setText"):
            btn.setText("Updating...")
            btn.setEnabled(False)

        is_zip = (class_id == 9184)
        self.dl_worker = DownloadWorker(self.client, mod_id, target_dir, is_zip)

        def on_done(result_json):
            result = json.loads(result_json)
            self.registry.add(
                mod_id=mod_id,
                mod_name=reg_entry.get('mod_name', ''),
                file_name=result.get('file_name', ''),
                file_id=result.get('file_id'),
                file_date=result.get('file_date', ''),
                class_id=class_id,
            )
            self.available_updates.pop(mod_id_str, None)
            remaining = len(self.available_updates)
            if remaining > 0:
                self.update_all_btn.setText(f"Update All ({remaining})")
            else:
                self.update_all_btn.setVisible(False)
                self.status_label.setText("All mods are up to date.")

            if self._update_queue:
                next_id = self._update_queue.pop(0)
                self.update_single(next_id)
            else:
                self.refresh()

        def on_error(msg):
            print(f"[UPDATE ERROR] mod {mod_id_str}: {msg}")
            if self._update_queue:
                next_id = self._update_queue.pop(0)
                self.update_single(next_id)
            else:
                self.refresh()

        self.dl_worker.finished.connect(on_done)
        self.dl_worker.error.connect(on_error)
        self.dl_worker.start()

    def update_all(self):
        if not self.available_updates:
            return

        ids = list(self.available_updates.keys())
        self.update_all_btn.setEnabled(False)
        self.update_all_btn.setText("Updating...")
        self.status_label.setText(f"Updating 0/{len(ids)}...")

        self._update_queue = ids[1:]
        self._update_total = len(ids)
        self._update_done = 0

        def tracked_update(mid_str, btn=None):
            mod_id = int(mid_str)
            reg_entry = self.registry.get(mod_id)
            if not reg_entry:
                if self._update_queue:
                    next_id = self._update_queue.pop(0)
                    tracked_update(next_id)
                else:
                    self._finish_update_all()
                return

            old_name = reg_entry.get('file_name', '')
            class_id = reg_entry.get('class_id')
            subfolder = PATH_MAP.get(class_id, "UserData/Mods")
            target_dir = os.path.normpath(os.path.join(self.game_path, subfolder))

            old_path = os.path.join(target_dir, old_name)
            if os.path.exists(old_path):
                if os.path.isdir(old_path):
                    shutil.rmtree(old_path)
                else:
                    os.remove(old_path)

            is_zip = (class_id == 9184)
            self.dl_worker = DownloadWorker(self.client, mod_id, target_dir, is_zip)

            def on_done(result_json):
                result = json.loads(result_json)
                self.registry.add(
                    mod_id=mod_id,
                    mod_name=reg_entry.get('mod_name', ''),
                    file_name=result.get('file_name', ''),
                    file_id=result.get('file_id'),
                    file_date=result.get('file_date', ''),
                    class_id=class_id,
                )
                self.available_updates.pop(mid_str, None)
                self._update_done += 1
                self.status_label.setText(f"Updating {self._update_done}/{self._update_total}...")

                if self._update_queue:
                    next_id = self._update_queue.pop(0)
                    tracked_update(next_id)
                else:
                    self._finish_update_all()

            def on_error(msg):
                print(f"[UPDATE ALL ERROR] mod {mid_str}: {msg}")
                self._update_done += 1
                self.status_label.setText(f"Updating {self._update_done}/{self._update_total}...")
                if self._update_queue:
                    next_id = self._update_queue.pop(0)
                    tracked_update(next_id)
                else:
                    self._finish_update_all()

            self.dl_worker.finished.connect(on_done)
            self.dl_worker.error.connect(on_error)
            self.dl_worker.start()

        tracked_update(ids[0])

    def _finish_update_all(self):
        self.update_all_btn.setEnabled(True)
        remaining = len(self.available_updates)
        if remaining > 0:
            self.update_all_btn.setText(f"Update All ({remaining})")
            self.status_label.setText(f"{remaining} update(s) remaining.")
        else:
            self.update_all_btn.setVisible(False)
            self.status_label.setText("All mods updated.")
        self.refresh()

    def get_dir_size(self, path):
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total += os.path.getsize(fp)
        except:
            return 0
        return total / (1024 * 1024)

    def delete_file(self, relative_path, mod_id=None):
        full_path = os.path.normpath(os.path.join(self.game_path, relative_path))
        filename = os.path.basename(relative_path)

        if QMessageBox.question(None, "Uninstall", f"Permanently delete {filename}?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                if os.path.exists(full_path):
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path)
                    else:
                        os.remove(full_path)
                if mod_id:
                    self.registry.remove(int(mod_id))
                self.refresh()
                return True
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to delete: {str(e)}")
                return False
        return False

    def clear_list(self):
        while self.layout_content.count():
            child = self.layout_content.takeAt(0)
            if child.widget(): child.widget().deleteLater()
