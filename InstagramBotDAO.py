import config
import uuid
from sqlalchemy import Column, Integer, DateTime, Text, Boolean


class InstgaramImageRss(config.Base):
    __tablename__ = 'instagram_image_rss'
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Text, primary_key=True, default=lambda: uuid.uuid4().hex)
    published = Column(DateTime)
    local_name = Column(Text)
    local_path = Column(Text)
    rss_webstagram_id = Column(Text)
    summary = Column(Text)
    media_url = Column(Text)
    image_hash = Column(Text)
    creation_time = Column(DateTime)
    link = Column(Text)
    sended = Column(Boolean)
    username = Column(Text)

    def __str__(self):
        import json
        return json.dumps(self.__dict__, default=str)


class InstagramSubscription(config.Base):
    __tablename__ = 'instagram_subscription'
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Text, primary_key=True, default=lambda: uuid.uuid4().hex)
    username = Column(Text, primary_key=True, unique=True)
    last_check_datetime = Column(DateTime)
    subscribed = Column(Boolean)


class Chat(config.Base):
    __tablename__ = 'chats'
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Text, primary_key=True, default=lambda: uuid.uuid4().hex)
    chat_id = Column(Integer)
    admin = Column(Boolean)
    tg_ans = Column(Text)

config.Base.metadata.create_all(config.engine)
