import feedparser
import shutil
import config
import os
from datetime import datetime
import Utils
import tempfile
import hashlib
import logging
from InstagramBotDAO import InstgaramImageRss, InstagramSubscription
from urllib.parse import urlparse
import threading
import asyncio
from multiprocessing.pool import ThreadPool


async def parse_feed(username, url, data_directory):
    session = config.Session()
    try:
        stop = False
        feed = feedparser.parse(url)
        for x in feed['entries']:
            if stop:
                break
            current_data = datetime.strptime(x['published'], '%a, %d %b %Y %H:%M:%S %z')
            for i, media in enumerate(x['media_thumbnail']):
                logging.info('processing {} for {}'.format(i, username))
                same_id = session.query(InstgaramImageRss).filter(InstgaramImageRss.rss_webstagram_id==x['id']).all()
                # print(same_id)
                if same_id is not None and len(same_id) > 0:
                    stop = True
                    break
                current_tmp_filename = os.path.join(tempfile._get_default_tempdir(), next(tempfile._get_candidate_names()))
                await Utils.download(media['url'], path=current_tmp_filename)
                current_image_hash = hashlib.sha256(open(current_tmp_filename, 'rb').read()).hexdigest()
                same_hash = session.query(InstgaramImageRss).filter(InstgaramImageRss.image_hash==current_image_hash).all()
                # import json
                # print(json.dumps(x, indent=4))
                if same_hash:
                    os.remove(current_tmp_filename)
                    stop = True
                    break
                current_filename = urlparse(x["link"]).path[3:] + "_" + str(i) + '.jpg'
                new_path = os.path.join(data_directory, current_filename)
                shutil.move(current_tmp_filename, new_path)
                current_image_rss = InstgaramImageRss()
                current_image_rss.published = current_data
                current_image_rss.local_name = current_filename
                current_image_rss.local_path = new_path
                current_image_rss.rss_webstagram_id = x['id']
                current_image_rss.summary = x['summary_detail']['value']
                current_image_rss.media_url = media['url']
                current_image_rss.image_hash = current_image_hash
                current_image_rss.creation_time = datetime.now()
                current_image_rss.link = x['link']
                current_image_rss.sended = False
                current_image_rss.username = username
                # print(current_image_rss)
                session.add(current_image_rss)
                try:
                    session.commit()
                except Exception:
                    session.rollback()
    except Exception as e:
        logging.exception(str(e))
    finally:
        session.close()


async def parse_user(username):
    current_user_directory = os.path.join(config.DATA_DIRECTORY, username)
    if not os.path.exists(current_user_directory):
        os.makedirs(current_user_directory)
    logging.info('scrapping rss for {} started'.format(username))
    await parse_feed(username, 'https://web.stagram.com/rss/n/{}'.format(username), current_user_directory)


async def get_info(username):
    try:
        feed = feedparser.parse('https://web.stagram.com/rss/n/{}'.format(username))
        if feed is None or feed['bozo'] == 1 or 'bozo_exception' in feed:
            return None
        else:
            return "Заголовок ленты: {}, страница {}"\
                .format(feed['feed']['title'] if 'feed' in feed and 'title' in feed['feed'] else None,
                        'публичная, есть фото' if 'entries' in feed and len(feed['entries']) > 0 else 'приватная или пустая')
    except Exception as e:
        return None


class InstagramRssParser:

    async def _scrape(self, username):
        session = config.Session()
        try:
            current_sunscription = session.query(InstagramSubscription).filter(InstagramSubscription.username == username).first()
            await parse_user(username)
            current_sunscription.last_check_datetime = datetime.now()
            session.add(current_sunscription)
            try:
                session.commit()
            except Exception as e:
                logging.exception(e)
                session.rollback()
        except Exception as e:
            logging.exception(e)
        finally:
            session.close()

    async def run(self):
        logging.info('starting subscription')
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
                    await  self._scrape(username.username)
            except Exception as e:
                logging.exception(e)
            finally:
                session.close()
            logging.info('sleeping')
            await asyncio.sleep(config.TIME_SLEEP)
