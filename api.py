import urllib.request
import urllib.parse
import json
import ssl
from urllib.error import HTTPError, URLError

from ui.common.maps import CLASS_MAP

class ModClient:
    def __init__(self, api_key):
        self.game_id = 0
        self.headers = {
            "x-api-key": api_key,
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def request(self, endpoint, params=None):
        if params is None: params = {}
        base_url = "https://api.curseforge.com/v1" + endpoint

        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{base_url}?{query_string}"
        else:
            url = base_url

        req = urllib.request.Request(url, headers=self.headers, method='GET')
        context = ssl.create_default_context()

        try:
            with urllib.request.urlopen(req, context=context) as response:
                return json.loads(response.read())
        except HTTPError as e:
            raise e
        except URLError as e:
            raise Exception(f"Connection Error: {e.reason}")

    def init_connection(self):
        try:
            print("DEBUG: Searching for 'Hytale'...")
            games_data = self.request("/games", {"index": 0, "pageSize": 50})
            hytale = next((g for g in games_data.get('data', []) if g['name'] == "Hytale"), None)

            if hytale:
                self.game_id = hytale['id']
                print(f"DEBUG: Hytale Found (ID: {self.game_id})")
                return f"Connected to Hytale"
            else:
                return "Error: Hytale not found in API"

        except Exception as e:
            return f"Connection Failed: {str(e)}"

    def search(self, query, class_name="mods", sort_field=2, sort_order="desc", index=0):
        target_class_id = CLASS_MAP.get(class_name.lower())

        print(f"\n[SEARCH] '{query}' (Category: {class_name} [ID: {target_class_id}], Index: {index})")

        params = {
            "gameId": self.game_id,
            "searchFilter": query,
            "sortField": sort_field,
            "sortOrder": sort_order,
            "pageSize": 20,
            "index": index
        }

        if target_class_id:
            params["classId"] = int(target_class_id)

        try:
            res = self.request("/mods/search", params)
            data = res.get('data', [])
            total = res.get('pagination', {}).get('totalCount', 0)

            print(f"[API] Found {len(data)} results (Total: {total})")
            return data, total

        except Exception as e:
            print(f"[SEARCH ERROR] {e}")
            return [], 0

    def discover_hytale_categories(self):
        print(f"\n--- DISCOVERING CATEGORIES FOR GAME {self.game_id} ---")
        try:
            res = self.request("/categories", {"gameId": self.game_id})
            categories = res.get('data', [])

            for cat in categories:
                print(f"Name: {cat['name']} | ID: {cat['id']} | IsClass: {cat.get('isClass')}")

        except Exception as e:
            print(f"Discovery failed: {e}")

    def get_mod(self, mod_id):
        res = self.request(f"/mods/{mod_id}")
        return res.get('data', {})

    def get_download_url(self, mod_id):
        res = self.request(f"/mods/{mod_id}/files")
        files = res.get('data', [])
        files.sort(key=lambda x: x['fileDate'], reverse=True)
        if not files:
            raise Exception("No files found")

        latest = files[0]
        url = latest.get('downloadUrl')

        if not url:
            file_id = latest['id']
            try:
                fallback = self.request(f"/mods/{mod_id}/files/{file_id}/download-url")
                url = fallback.get('data')
            except Exception:
                url = (
                    f"https://edge.forgecdn.net/files/"
                    f"{str(file_id)[:4]}/{str(file_id)[4:]}/{latest['fileName']}"
                )

        return {
            "url": url,
            "name": latest['fileName'],
            "file_id": latest['id'],
            "file_date": latest.get('fileDate', ''),
        }

    def download_file(self, url, dest_path):
        print(f"DEBUG: Downloading {url}")
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
            out_file.write(response.read())