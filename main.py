import logging
import re
import time

import requests

from bs4 import BeautifulSoup

from config import webhook_url, last_comic


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "[%(levelname)s] [%(asctime)s] %(message)s",
    "%d/%m/%Y %H:%M:%S",
)
handler.setFormatter(formatter)
log.addHandler(handler)


while True:

    # get the website HTML
    log.debug("Getting dinosandcomics html")
    html = requests.get("https://dinosandcomics.com/").text

    # create a BeautifulSoup object
    log.debug("parsing html using beautifulsoup")
    soup = BeautifulSoup(html, features="html5lib")

    # find the comic image displayed on the page
    # it's in an img tag with the class "attachment-medium_large size-medium_large wp-post-image"
    log.debug("finding comic on the page")
    img_tag = soup.find(
        name="img",
        attrs={"class": "attachment-medium_large size-medium_large wp-post-image"},
    )

    # extract image URL and check whether it's the same one as previous iteration
    img_url = img_tag.attrs["src"]
    log.debug("found %s, comparing to previous comic", img_url)
    if img_url == last_comic:
        log.info("found comic, same as previous iteration, waiting 30 minutes")
        time.sleep(30 * 60)
        continue
    else:
        last_comic = img_url

    # image might be smaller than original, replace with full size url
    # [...]664-768x768.png -> [...]664.png
    log.debug("subbing url for full image url")
    full_url = re.sub(r"-\d+x\d+", "", img_url)

    # get the file extension from url
    log.debug("finding file extension")
    ext = re.search(r".*.(jpeg|jpg|png|webp)", full_url).group(1)

    # get the image bytes
    log.debug("retrieving image bytes")
    response = requests.get(full_url, stream=True)
    data = response.raw.data

    # post to discord
    log.debug("posting to discord")
    requests.post(
        webhook_url,
        files={f"comic.{ext}": data},
    )

    # done, now wait to check again
    log.debug("posted to discord, waiting 30 minutes")
    time.sleep(30 * 60)
