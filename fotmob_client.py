import time
import requests

BASE_URL = "https://www.fotmob.com"

class FotMobError(Exception):
    pass

class FotMobClient:
    def __init__(self, timeout=30, retries=3):
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; FotMobDataExplorer/1.0)",
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://www.fotmob.com/",
        })

    def get(self, path, params=None):
        url = BASE_URL + path
        last_error = None
        for attempt in range(self.retries):
            try:
                response = self.session.get(url, params=params or {}, timeout=self.timeout)
                if response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
                try:
                    return response.json()
                except ValueError as exc:
                    raise FotMobError(
                        f"FotMob devolvió una respuesta que no es JSON. HTTP {response.status_code}"
                    ) from exc
            except requests.RequestException as exc:
                last_error = exc
                if attempt < self.retries - 1:
                    time.sleep(1.5 * (attempt + 1))
        raise FotMobError(f"Error consultando {url}: {last_error}")
