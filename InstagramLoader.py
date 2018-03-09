from instaloader import instaloader
import config
import multiprocessing
import asyncio
import logging
import os
import re
from collections import defaultdict
import datetime
import json
from InstagramBotDAO import InstagramSubscription, InstagramImageNoRss


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


class InstagramLoaderRegistering:
    def __init__(self, folder_path):
        self.folder_for_registering = folder_path

    def register(self):
        session = config.Session()
        try:
            for username in os.listdir(self.folder_for_registering):
                current_directory = os.path.join(self.folder_for_registering, username)
                filepaths = set([])
                date_to_files = defaultdict(list)
                for file in os.listdir(current_directory):
                    current_filepath = os.path.join(current_directory, file)
                    filepaths.add(current_filepath)
                    parsed_filename = re.search('(?P<date>.*)_UTC(_((?P<index>\d+)|(?P<type>[\w|_]+)))?\.(?P<extension>jpg|json|txt|mp4)', file)
                    if not parsed_filename:
                        logging.warning('ignored file = {}'.format(current_filepath))
                        continue
                    filetype = parsed_filename.group('extension')
                    if filetype not in ['jpg', 'mp4']:
                        continue
                    current_filedate = parsed_filename.group('date')
                    current_filedatedate = datetime.datetime.strptime(current_filedate, "%Y-%m-%d_%H-%M-%S")
                    index = parsed_filename.group('index') or 1
                    ret = session.query(InstagramImageNoRss).\
                        filter(InstagramImageNoRss.publication_index==index).\
                        filter(InstagramImageNoRss.username==username).\
                        filter(InstagramImageNoRss.local_path==current_filepath).\
                        filter(InstagramImageNoRss.published==current_filedatedate).all()
                    if ret and len(ret) > 0:
                        continue
                    current_db_object = InstagramImageNoRss()
                    current_db_object.username = username
                    current_db_object.local_path = current_filepath
                    current_db_object.published = current_filedatedate
                    local_path_txt = os.path.join(current_directory, current_filedate + '_UTC.txt')
                    if os.path.exists(local_path_txt):
                        current_db_object.local_path_txt = local_path_txt
                        with open(local_path_txt, 'r', encoding='utf8') as localtxtf:
                            current_db_object.text_data = '\n'.join(localtxtf.readlines())
                    local_path_json = os.path.join(current_directory, current_filedate + '_UTC.json')
                    if os.path.exists(local_path_json):
                        current_db_object.local_path_json = local_path_json
                        with open(local_path_json, 'r', encoding='utf8') as localjsonf:
                            current_db_object.json_data = json.dumps(json.loads(' '.join(localjsonf.readlines())))
                    comments_path = os.path.join(current_directory, current_filedate + '_UTC_comments.json')
                    if os.path.exists(comments_path):
                        current_db_object.comments_path = comments_path
                        with open(comments_path, 'r', encoding='utf8') as commentsjsonf:
                            current_db_object.comments_data = json.dumps(json.loads(' '.join(commentsjsonf.readlines())))
                    current_db_object.sended = False
                    current_db_object.publication_index = index
                    print(filetype, current_db_object)
        except Exception as e:
            logging.exception(e)
        finally:
            session.close()

    async def run(self):
        logging.info('starting instaloader registering')
        while True:
            session = config.Session()
            try:
                self.register()
            except Exception as e:
                logging.exception(e)
            finally:
                session.close()
            logging.info('sleeping instaloader registering...')
            await asyncio.sleep(config.TIME_SLEEP_REGISTER)
            logging.info('waking up registering')


def main():
    instloader = InstagramLoader(config.INSTAGRAM_PARSER_LOGIN, config.INSTAGRAM_PARSER_PASSW)
    instregister = InstagramLoaderRegistering(config.DATA_DIRECTORY_NO_RSS)
    loop = asyncio.get_event_loop()
    # loop.create_task(instloader.run())
    loop.create_task(instregister.run())
    loop.run_forever()


if __name__ == "__main__":
    main()
