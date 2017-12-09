# InstagramTelegramBot
Telegram Bot monitoring Instagram accounts and send photos
Now bot parsing RSS-feed of websta.me, getting photos with titles and send it to subscribers

Commands:
1. /start - adding chat to 
2. /admin token - adding user as administrator (other users can't subscribe and not getting photos, it's private bot)
3. %username% - getting menu for subscribe / unsubscribe / getting photos of username

config_local.py template
```
BOT_API_TOKEN = '''your token for bot by telegram'''
BOT_ADMIN_PASSWORD = 'password / token for bot admin'
KEY = '''encryption key for db'''
```
