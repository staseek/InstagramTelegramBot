import logging
import instagrapi
from instagrapi.exceptions import LoginRequired
from pathlib import Path
import config
from typing import Optional


class SessionStorage:
    def __init__(self):
        self.SESSION_DIR = Path('''sessions''')
        self.SESSION_DIR.mkdir(parents=True, exist_ok=True)

    def get_session(self, session_name: str) -> Path:
        current_filename = self.SESSION_DIR / Path(session_name)
        return current_filename if current_filename.exists() else None

    def create_session(self, session_name: str) -> Path:
        current_filename = self.SESSION_DIR / Path(session_name)
        return current_filename


class InstagramModule:
    def __init__(self, login: str, password: str, logger: Optional[logging.Logger] = None):
        self.logger = logger if logger else logging.getLogger('InstagramModule')
        self.logger.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)
        self.login = login
        self.password = password
        self.client = instagrapi.Client()
        self.session_storage = SessionStorage()
        self.session = self.client.load_settings(self.session_storage.get_session(login)) if self.session_storage.get_session(login) else None
        login_via_session = False
        login_via_pw = False
        if self.session:
            try:
                self.client.set_settings(self.session)
                self.client.login(login, password)

                # check if session is valid
                try:
                    self.client.get_timeline_feed()
                except LoginRequired:
                    self.logger.info("Session is invalid, need to login via username and password")

                    old_session = self.client.get_settings()

                    # use the same device uuids across logins
                    self.client.set_settings({})
                    self.client.set_uuids(old_session["uuids"])

                    self.client.login(login, password)
                login_via_session = True
            except Exception as e:
                self.logger.info("Couldn't login user using session information: %s" % e)

        if not login_via_session:
            try:
                self.logger.info("Attempting to login via username and password. username: %s", login)
                if self.client.login(login, password):
                    login_via_pw = True
                    self.client.dump_settings(self.session_storage.create_session(self.login))
            except Exception as e:
                logger.info("Couldn't login user using username and password: %s" % e)

        if not login_via_pw and not login_via_session:
            raise Exception("Couldn't login user with either password or session")

    def get_feed(self, username):
        user_info = self.client.user_info_by_username(username)
        print(user_info)


if __name__ == "__main__":
    instagram_module = InstagramModule(config.LOGIN, config.PASSWORD)
    instagram_module.get_feed("durov")
