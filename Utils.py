import aiohttp
import logging
from contextlib import closing

# async def download_file(url, path):
#     r = requests.get(url, stream=True)
#     if r.status_code == 200:
#         async with open(path, 'wb') as f:
#             for chunk in r.iter_content(1024):
#                 f.write(chunk)

async def download(url, path, chunk_size=1<<15):
    logging.info('downloading %s', path)
    with closing(aiohttp.ClientSession()) as session:
        response = await session.get(url)
        with closing(response), open(path, 'wb') as file:
            while True:
                chunk = await response.content.read(chunk_size)
                if not chunk:
                    break
                file.write(chunk)
    logging.info('done {}'.format(path))