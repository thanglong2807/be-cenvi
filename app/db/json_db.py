import json
from pathlib import Path
from threading import Lock

class JsonDB:
    _locks = {}

    def __init__(self, file_path: str):
        self.path = Path(file_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if file_path not in self._locks:
            self._locks[file_path] = Lock()

        self.lock = self._locks[file_path]

        if not self.path.exists():
            self._write({"last_id": 0, "items": []})

    def _read(self):
        with self.lock:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)

    def _write(self, data):
        with self.lock:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def all(self):
        return self._read()["items"]

    def insert(self, item: dict):
        data = self._read()
        data["last_id"] += 1
        item["id"] = data["last_id"]
        data["items"].append(item)
        self._write(data)
        return item

    def find_by(self, key, value):
        return next((x for x in self.all() if x.get(key) == value), None)
