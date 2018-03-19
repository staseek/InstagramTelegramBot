import telepot
import telepot.aio
from telepot.aio.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import InstagramFeedParserRSS
import traceback
import re
import Utils
import tempfile
from sqlalchemy import and_
from sqlalchemy import desc
from InstagramBotDAO import *
from InstagramLoader import *
TOKEN = config.BOT_API_TOKEN


def main():
    message_with_inline_keyboard = None

    async def send_media_instaloader():
        while True:
            session = config.Session()
            try:
                pics_to_send = session.query(InstagramImageNoRss).filter(InstagramImageNoRss.sended == False).all()
                for pic_to_send in pics_to_send:
                    with open(pic_to_send.local_path, 'rb') as mediaf:
                        for chat_id in [x.chat_id for x in session.query(Chat).filter(Chat.admin == True).all()]:
                            if pic_to_send.local_path.endswith('.jpg'):
                                logging.info('sending photo')
                                await bot.sendPhoto(chat_id=chat_id, photo=mediaf, caption="/{} from instaloader".format(pic_to_send.username))
                                logging.info('sended photo')
                            elif pic_to_send.local_path.endswith('.mp4'):
                                logging.info('sending video')
                                await bot.sendVideo(chat_id=chat_id, video=mediaf, caption="/{} index={} from instaloader".format(pic_to_send.username, pic_to_send.text_data))
                                logging.info('sended video')
                            else:
                                await bot.sendMessage(chat_id=chat_id, text='Not understand type please debug me. {}'.format(pic_to_send))
                                continue
                            if pic_to_send.text_data is not None and len(pic_to_send.text_data) > 0:
                                await bot.sendMessage(chat_id=chat_id, text='/{} index={} from instaloader with text {}'.format(pic_to_send.username, pic_to_send.publication_index, pic_to_send.text_data))
                            if config.SEND_JSON_DATA and pic_to_send.json_data is not None and len(pic_to_send.json_data) > 0:
                                await bot.sendMessage(chat_id=chat_id, text='/{} index={}from instaloader with json data\n{}'.format(pic_to_send.username, pic_to_send.text_data, json.dumps(json.loads(pic_to_send.json_data), indent=4))[:4000])
                            if pic_to_send.geolocation_data is not None and len(pic_to_send.geolocation_data) > 0:
                                geo = pic_to_send.geolocation_data
                                await bot.sendMessage(chat_id=chat_id, text='/{} from instaloader with geolocation data\n{}'.format(pic_to_send.username, geo))
                                geo_parsed = re.search('http(s)?:\/\/maps.google.com\/maps\?q=(?P<longitude>(\d|\.)+)\,(?P<latitude>(\d|\.)+)&.*', geo)
                                if geo_parsed:
                                    longitude = geo_parsed.group('longitude')
                                    latitude = geo_parsed.group('latitude')
                                    for zoom in range(0,18,3):
                                        current_url = 'https://static-maps.yandex.ru/1.x/?ll={},{}&size=450,450&z={}&l=map&pt={},{}'.format(latitude, longitude, zoom, latitude, longitude)
                                        current_tmp_filename = os.path.join(tempfile._get_default_tempdir(),
                                                                        next(tempfile._get_candidate_names()))
                                        await Utils.download(current_url, path=current_tmp_filename)
                                        with open(current_tmp_filename, 'rb') as cf:
                                            await bot.sendPhoto(chat_id=chat_id, photo=cf, caption='/{} with geolocation at {}'.format(pic_to_send.username, zoom))
                                        os.remove(current_tmp_filename)
                                        await asyncio.sleep(.2)
                            if pic_to_send.comments_data is not None and len(pic_to_send.comments_data):
                                for comment in json.loads(pic_to_send.comments_data):
                                    await bot.sendMessage(chat_id=chat_id, text='/{} комментарий от {} запощен в {} с текстом:\n{}'
                                                          .format(pic_to_send.username,
                                                                  comment['owner']['username'],
                                                                  datetime.datetime.fromtimestamp(int(comment['created_at'])).strftime('%Y-%m-%d %H:%M:%S'),
                                                                  comment['text']))
                            pic_to_send.sended = True
                            session.add(pic_to_send)
                            try:
                                session.commit()
                            except Exception as e:
                                logging.exception(e)
                                session.rollback()

            except Exception as e:
                logging.exception(e)
                for chat_id in [x.chat_id for x in session.query(Chat).filter(Chat.admin == True).all()]:
                    await bot.sendMessage(chat_id=chat_id, text='Exception {} with {}'.format(str(e), traceback.format_exc()))
            finally:
                session.close()
            await asyncio.sleep(config.TIME_SLEEP_SENDER)

    async def send_pictures_rss():
        while True:
            session = config.Session()
            try:
                pics_to_send = session.query(InstgaramImageRss).filter(InstgaramImageRss.sended == False).all()
                for pic_to_send in pics_to_send:
                    with open(pic_to_send.local_path, 'rb') as picf:
                        for chat_id in [x.chat_id for x in session.query(Chat).filter(Chat.admin == True).all()]:
                            current_text = '/{} from RSS feed with text: {} '.format(pic_to_send.username, pic_to_send.summary)
                            short_text = '/{} from RSS feed photo'.format(pic_to_send.username)
                            await bot.sendPhoto(chat_id=chat_id, photo=picf, caption=short_text)
                            await bot.sendMessage(chat_id=chat_id, text=current_text)
                    pic_to_send.sended = True
                    session.add(pic_to_send)
                    try:
                        session.commit()
                    except Exception as e:
                        logging.exception(e)
                        session.rollback()
            except Exception as e:
                logging.exception(e)
                for chat_id in [x.chat_id for x in session.query(Chat).filter(Chat.admin == True).all()]:
                    await bot.sendMessage(chat_id=chat_id, text='Exception {} with {}'.format(str(e), traceback.format_exc()))
            finally:
                session.close()
            await asyncio.sleep(config.TIME_SLEEP_SENDER)

    async def on_chat_message(msg):
        session = config.Session()
        try:
            content_type, chat_type, chat_id = telepot.glance(msg)
            # print('Chat:', content_type, chat_type, chat_id)

            if content_type != 'text':
                return

            command = msg['text'][:].lower()
            if 'text' in msg and msg['text'] == '/start':
                new_chat_info = session.query(Chat).filter(Chat.chat_id == chat_id).first()
                if new_chat_info is None:
                    new_chat_info = Chat(chat_id=chat_id, admin=False, tg_ans=str(msg))
                    await bot.sendMessage(chat_id, u'Шо?! Новый пользователь?!')
                else:
                    await bot.sendMessage(chat_id, u'А я тебя уже знаю')
                session.add(new_chat_info)
                try:
                    session.commit()
                except Exception as e:
                    logging.exception(e)
                    session.rollback()
            elif command.startswith('/admin'):
                passw = re.search('\/admin\s+(?P<passw>\w+)', msg['text'])
                if passw and passw.group('passw') == config.BOT_ADMIN_PASSWORD:
                    current_chat_info = session.query(Chat).filter(Chat.chat_id == chat_id).first()
                    current_chat_info.admin = True
                    session.add(current_chat_info)
                    try:
                        session.commit()
                    except Exception as e:
                        session.rollback()
                    await bot.sendMessage(chat_id, u'Слушаю и повинуюсь, хозяин')
                else:
                    await bot.sendMessage(chat_id, u'ЭЭЭ ТЫ КТО ТАКОЙ? ДАВАЙ ДО СВИДАНИЯ!')
            elif command.startswith('/subscriptions') and session.query(Chat).filter(Chat.chat_id == chat_id and Chat.admin == True):
                is_succ = session.query(Chat).filter(and_(Chat.chat_id == chat_id,  Chat.admin == True)).all()
                if not is_succ:
                    return
                current_message = ''
                for subscription in session.query(InstagramSubscription).all():
                    if len(current_message) > 200:
                        current_message += ' ' + str(subscription.username)
                        await bot.sendMessage(chat_id, str(current_message))
                    else:
                        current_message += ' ' + str(subscription.username)

            else:
                is_succ = session.query(Chat).filter(and_(Chat.chat_id == chat_id, Chat.admin == True)).all()
                if command.startswith('/'):
                    command = command[1:]
                infomation_about_user = await InstagramFeedParserRSS.get_info(command)
                if infomation_about_user is None:
                    await bot.sendMessage(chat_id, "Проблема с пользователем {} его rss-лента не парсится".format(command))
                elif is_succ is not None and len(is_succ) > 0:
                    await bot.sendMessage(chat_id, infomation_about_user)
                    markup = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text='подписаться', callback_data=json.dumps({'action': 'subscribe', 'username': command}))],
                        [InlineKeyboardButton(text='отписаться', callback_data=json.dumps({'action': 'unsubscribe', 'username': command}))],
                        [InlineKeyboardButton(text='прислать последние 3 фото RSS ленты', callback_data=json.dumps({'action': 'last', 'username': command}))],
                        [InlineKeyboardButton(text='прислать все фото, что есть RSS', callback_data=json.dumps({'action': 'all', 'username': command}))],
                        [InlineKeyboardButton(text='прислать последние 3 фото Instaloader',
                                              callback_data=json.dumps({'action': 'last', 'username': command}))],
                        [InlineKeyboardButton(text='прислать все фото, что есть Instaloader',
                                              callback_data=json.dumps({'action': 'all', 'username': command}))],
                    ])
                    global message_with_inline_keyboard
                    message_with_inline_keyboard = await bot.sendMessage(chat_id, 'что прикажете?', reply_markup=markup)
                else:
                    await bot.sendMessage(chat_id, 'Вы не администратор. Вам нельзя.')
        except Exception as e:
            logging.exception(e)
            for chat_id in [x.chat_id for x in session.query(Chat).filter(Chat.admin == True).all()]:
                await bot.sendMessage(chat_id=chat_id,
                                      text='Exception {} with {}'.format(str(e), traceback.format_exc()))
        finally:
            session.close()

    async def on_callback_query(msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        data = json.loads(data)
        session = config.Session()
        try:
            subscriptions = session.query(InstagramSubscription).filter(InstagramSubscription.username == data['username']).all()
            if subscriptions is None or len(subscriptions) == 0:
                current_subscription = InstagramSubscription()
            else:
                current_subscription = subscriptions[0]
            current_subscription.username = data['username']
            if data['action'] == 'subscribe':
                current_subscription.subscribed = True
                session.add(current_subscription)
                await bot.sendMessage(from_id, 'subscribed to {}'.format(data['username']))
                try:
                    session.commit()
                except Exception as e:
                    logging.exception(e)
                    session.rollback()
            elif data['action'] == 'unsubscribe':
                current_subscription.subscribed = False
                await bot.sendMessage(from_id, 'unbscribed from {}'.format(data['username']))
                try:
                    session.commit()
                except Exception as e:
                    logging.exception(e)
                    session.rollback()
            elif data['action'] == 'last_rss':
                photos = session.query(InstgaramImageRss).filter(InstgaramImageRss.username == data['username']).order_by(desc(InstgaramImageRss.published)).limit(3).all()
                await send_rss_photos(from_id, photos, session)
            elif data['action'] == 'all_rss':
                photos = session.query(InstgaramImageRss).filter(InstgaramImageRss.username == data['username']).order_by(InstgaramImageRss.published).all()
                await send_rss_photos(from_id, photos, session)
        except Exception as e:
            logging.exception(e)
            for chat_id in [x.chat_id for x in session.query(Chat).filter(Chat.admin == True).all()]:
                await bot.sendMessage(chat_id=chat_id,
                                      text='Exception {} with {}'.format(str(e), traceback.format_exc()))
        finally:
            session.close()

    async def send_rss_photos(from_id, photos, session):
        if photos is None or len(photos) == 0:
            await bot.sendMessage(from_id, 'Нет фото')
        else:
            for photo in photos:
                with open(photo.local_path, 'rb') as pf:
                    await bot.sendPhoto(chat_id=from_id, photo=pf, caption=photo.summary)
                    await bot.sendMessage(chat_id=from_id, text=photo.summary)
                photo.sended = True
                session.add(photo)
                try:
                    session.commit()
                except Exception as e:
                    session.rollback()

    def on_chosen_inline_result(msg):
        result_id, from_id, query_string = telepot.glance(msg, flavor='chosen_inline_result')
        return



    rss_parser = InstagramFeedParserRSS.InstagramRssParser()
    bot = telepot.aio.Bot(TOKEN)
    answerer = telepot.aio.helper.Answerer(bot)

    loop = asyncio.get_event_loop()
    loop.create_task(MessageLoop(bot, {'chat': on_chat_message,
                                       'callback_query': on_callback_query,
                                       'chosen_inline_result': on_chosen_inline_result}).run_forever())
    loop.create_task(send_pictures_rss())
    loop.create_task(send_media_instaloader())
    loop.create_task(rss_parser.run())
    # instaloader threads
    # instloader = InstagramLoader(config.INSTAGRAM_PARSER_LOGIN, config.INSTAGRAM_PARSER_PASSW)
    # instregister = InstagramLoaderRegistering(config.DATA_DIRECTORY_NO_RSS)
    # loop.create_task(instloader.run())
    # loop.create_task(instregister.run())
    loop.run_forever()


if __name__ == "__main__":
    main()
