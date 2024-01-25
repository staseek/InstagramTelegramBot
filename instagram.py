from instagrapi import Client
from pathlib import Path
import config

class SessionStorage:
    def __init__(self):
        self.SESSION_DIR = Path('''sessions''')
        self.SESSION_DIR.mkdir(parents=True, exist_ok=True)

    def get_session(self, session_name: str) -> Path:
        return {self.SESSION_DIR} / Path(session_name)


class InstagramModule:
    def __init__(self, login: str, password: str):
        self.client = Client()
        self.session_storage = SessionStorage()
        self.client.load_settings(self.session_storage.get_session(login))


if __name__ == "__main__":
    instagram_module = InstagramModule(config.LOGIN, config.PASSWORD)
