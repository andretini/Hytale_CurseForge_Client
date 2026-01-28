import json
import os
import zipfile

from PySide6.QtCore import QThread, Signal


class SearchWorker(QThread):
    finished = Signal(list, int)
    error = Signal(str)

    def __init__(self, client, query, category="mods", sort_field=2, sort_order="desc", index=0):
        super().__init__()
        self.client = client
        self.query = query
        self.category = category
        self.sort_field = sort_field
        self.sort_order = sort_order
        self.index = index

    def run(self):
        try:
            print(self.category)
            mods, total = self.client.search(
                self.query,
                self.category,
                self.sort_field,
                self.sort_order,
                self.index
            )
            self.finished.emit(mods, total)
        except Exception as e:
            self.error.emit(str(e))


class DownloadWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, client, mod_id, target_dir, is_zip=False):
        super().__init__()
        self.client = client
        self.mod_id = mod_id
        self.target_dir = target_dir
        self.is_world = is_zip

    def run(self):
        try:
            file_data = self.client.get_download_url(self.mod_id)
            if not file_data['url']:
                raise Exception("No download URL found")

            zip_path = os.path.join(self.target_dir, file_data['name'])

            self.client.download_file(file_data['url'], zip_path)

            result = {
                "file_name": file_data['name'],
                "file_id": file_data.get('file_id'),
                "file_date": file_data.get('file_date', ''),
            }

            if self.is_world and zip_path.endswith('.zip'):
                extract_path = os.path.join(self.target_dir, file_data['name'].replace('.zip', ''))

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)

                os.remove(zip_path)
                result["file_name"] = os.path.basename(extract_path)

            self.finished.emit(json.dumps(result))

        except Exception as e:
            self.error.emit(str(e))


class UpdateCheckWorker(QThread):
    finished = Signal(str)
    progress = Signal(int, int)
    error = Signal(str)

    def __init__(self, client, registry):
        super().__init__()
        self.client = client
        self.registry = registry

    def run(self):
        try:
            all_entries = self.registry.get_all()
            total = len(all_entries)
            updates = {}

            for i, (mod_id_str, entry) in enumerate(all_entries.items()):
                self.progress.emit(i + 1, total)
                try:
                    mod_data = self.client.get_mod(int(mod_id_str))
                    if not mod_data:
                        continue
                    latest_files = mod_data.get('latestFiles', [])
                    if latest_files:
                        latest_files.sort(key=lambda x: x.get('fileDate', ''), reverse=True)
                        latest_file_id = latest_files[0].get('id')
                        if latest_file_id and entry.get('file_id') != latest_file_id:
                            updates[mod_id_str] = mod_data
                except Exception as e:
                    print(f"[UPDATE CHECK] Failed for mod {mod_id_str}: {e}")

            self.finished.emit(json.dumps(updates))
        except Exception as e:
            self.error.emit(str(e))


class InitWorker(QThread):
    finished = Signal(str)

    def __init__(self, client): super().__init__(); self.client = client

    def run(self): self.finished.emit(self.client.init_connection())
