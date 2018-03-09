from instaloader import instaloader
import config
import multiprocessing
import asyncio
import logging
from InstagramBotDAO import InstagramSubscription


class InstagramLoader:
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.loader = instaloader.Instaloader(sleep=False,
                                              quiet=False,
                                              user_agent=None,
                                              dirname_pattern=config.DATA_DIRECTORY_NO_RSS + '{profile}',
                                              filename_pattern='{date:%Y-%m-%d_%H-%M-%S}',
                                              download_videos=instaloader.Tristate.always,
                                              download_video_thumbnails=instaloader.Tristate.always,
                                              download_geotags=instaloader.Tristate.always,
                                              save_captions=instaloader.Tristate.always,
                                              download_comments=instaloader.Tristate.always,
                                              save_metadata=instaloader.Tristate.always,
                                              max_connection_attempts=3)

    def _scrape(self, username):
        self.loader.main([username],
                         username=self.login.lower(),
                         password=self.password,
                         sessionfile=None,
                         max_count=None,
                         profile_pic=True,
                         profile_pic_only=False,
                         fast_update=True,
                         stories=True,
                         stories_only=False,
                         filter_str=None)

    async def scrape(self, username):
        process = multiprocessing.Process(target=self._scrape, args=(username,), )
        process.start()
        while process.is_alive():
            await asyncio.sleep(1)

    async def run(self):
        logging.info('starting instaloader')
        while True:
            session = config.Session()
            try:
                logging.info('starting data')
                session.query()
                usernames = session.query(InstagramSubscription).filter(InstagramSubscription.subscribed == True).all()
                if usernames is None:
                    logging.info('sleeping')
                    await asyncio.sleep(config.TIME_SLEEP)
                    continue
                for username in usernames:
                    logging.info('username===={}'.format(username))
                    await  self.scrape(username.username)
            except Exception as e:
                logging.exception(e)
            finally:
                session.close()
            logging.info('sleeping...')
            await asyncio.sleep(config.TIME_SLEEP)
            logging.info('waking up')


def main():
    instloader = InstagramLoader(config.INSTAGRAM_PARSER_LOGIN, config.INSTAGRAM_PARSER_PASSW)
    # res = instloader.scrape('nataliecheee')
    # print('res', res)
    loop = asyncio.get_event_loop()
    loop.create_task(instloader.run())
    loop.run_forever()


if __name__ == "__main__":
    main()
