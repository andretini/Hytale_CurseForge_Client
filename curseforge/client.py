"""CurseForge API Client - standalone module with minimal dependencies."""
import urllib.request
import urllib.parse
import json
import ssl
import os
import zipfile
import shutil
from urllib.error import HTTPError, URLError
from pathlib import Path


# Category mappings for Hytale
CLASS_MAP = {
    "mods": 9137,
    "prefabs": 9185,
    "worlds": 9184,
    "bootstrap": 9281,
    "translations": 10350,
}

PATH_MAP = {
    9137: "UserData/Mods",
    9184: "UserData/Saves",
    9185: "prefabs",
    9281: "bootstrap",
    10350: "translations",
}


class CurseForgeClient:
    """Low-level CurseForge API client."""

    BASE_URL = "https://api.curseforge.com/v1"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.game_id = 0  # Will be set after init_connection

    @property
    def headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "Accept": "application/json",
            "User-Agent": "HytaleCF-CLI/1.0",
        }

    def request(self, endpoint: str, params: dict = None) -> dict:
        """Make a GET request to the CurseForge API."""
        if params is None:
            params = {}

        url = self.BASE_URL + endpoint
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        req = urllib.request.Request(url, headers=self.headers, method='GET')
        context = ssl.create_default_context()

        try:
            with urllib.request.urlopen(req, context=context, timeout=30) as response:
                return json.loads(response.read())
        except HTTPError as e:
            if e.code == 403:
                raise Exception("Invalid API key or access denied")
            raise Exception(f"HTTP Error {e.code}: {e.reason}")
        except URLError as e:
            raise Exception(f"Connection Error: {e.reason}")

    def init_connection(self) -> bool:
        """Initialize connection and find Hytale game ID."""
        try:
            games_data = self.request("/games", {"index": 0, "pageSize": 50})
            hytale = next(
                (g for g in games_data.get('data', []) if g['name'] == "Hytale"),
                None
            )
            if hytale:
                self.game_id = hytale['id']
                return True
            return False
        except Exception:
            return False

    def search(
        self,
        query: str,
        category: str = "mods",
        sort_field: int = 2,
        sort_order: str = "desc",
        index: int = 0,
        page_size: int = 20,
    ) -> tuple:
        """
        Search for mods/worlds/etc.
        Returns (results_list, total_count)
        """
        class_id = CLASS_MAP.get(category.lower())

        params = {
            "gameId": self.game_id,
            "searchFilter": query,
            "sortField": sort_field,
            "sortOrder": sort_order,
            "pageSize": page_size,
            "index": index,
        }

        if class_id:
            params["classId"] = class_id

        res = self.request("/mods/search", params)
        data = res.get('data', [])
        total = res.get('pagination', {}).get('totalCount', 0)
        return data, total

    def get_mod(self, mod_id: int) -> dict:
        """Get detailed info about a specific mod."""
        res = self.request(f"/mods/{mod_id}")
        return res.get('data', {})

    def get_files(self, mod_id: int) -> list:
        """Get all files for a mod."""
        res = self.request(f"/mods/{mod_id}/files")
        return res.get('data', [])

    def get_latest_file(self, mod_id: int) -> dict:
        """Get the latest file for a mod."""
        files = self.get_files(mod_id)
        if not files:
            raise Exception(f"No files found for mod {mod_id}")
        files.sort(key=lambda x: x['fileDate'], reverse=True)
        return files[0]

    def download_file(self, url: str, dest_path: str, progress_callback=None) -> str:
        """
        Download a file from URL to dest_path.
        Returns the path to the downloaded file.
        """
        req = urllib.request.Request(url, headers=self.headers)
        context = ssl.create_default_context()

        with urllib.request.urlopen(req, context=context, timeout=60) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 8192

            with open(dest_path, 'wb') as out_file:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size:
                        progress_callback(downloaded, total_size)

        return dest_path

    def install_mod(
        self,
        mod_id: int,
        game_path: str,
        progress_callback=None,
    ) -> dict:
        """
        Download and install a mod.
        Returns info about the installed file.
        """
        mod_info = self.get_mod(mod_id)
        latest_file = self.get_latest_file(mod_id)

        download_url = latest_file.get('downloadUrl')
        if not download_url:
            raise Exception("Download URL not available for this mod")

        filename = latest_file['fileName']
        class_id = mod_info.get('classId', 9137)
        subpath = PATH_MAP.get(class_id, "UserData/Mods")
        install_dir = Path(game_path) / subpath
        install_dir.mkdir(parents=True, exist_ok=True)

        dest_path = install_dir / filename

        # Download
        self.download_file(str(download_url), str(dest_path), progress_callback)

        # If it's a world (zip), extract it
        if class_id == 9184 and filename.endswith('.zip'):
            extract_dir = install_dir
            with zipfile.ZipFile(dest_path, 'r') as zf:
                zf.extractall(extract_dir)
            os.remove(dest_path)
            filename = filename.replace('.zip', '')

        return {
            'mod_id': mod_id,
            'name': mod_info.get('name', ''),
            'filename': filename,
            'version': latest_file.get('displayName', ''),
            'file_id': latest_file.get('id'),
            'class_id': class_id,
            'path': str(dest_path),
        }

    def uninstall_mod(self, mod_info: dict, game_path: str) -> bool:
        """Remove an installed mod."""
        class_id = mod_info.get('class_id', 9137)
        subpath = PATH_MAP.get(class_id, "UserData/Mods")
        install_dir = Path(game_path) / subpath
        filename = mod_info.get('filename', '')

        if not filename:
            return False

        file_path = install_dir / filename
        if file_path.is_file():
            os.remove(file_path)
            return True
        elif file_path.is_dir():
            shutil.rmtree(file_path)
            return True
        return False

    def get_categories(self) -> list:
        """Get all categories for Hytale."""
        res = self.request("/categories", {"gameId": self.game_id})
        return res.get('data', [])
