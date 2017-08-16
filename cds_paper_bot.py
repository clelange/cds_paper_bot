"""Twitter bot to post latest CMS results."""
from __future__ import print_function
import os
import sys
import shutil
import logging
import subprocess
import daiquiri
import feedparser
from pylatexenc.latexwalker import LatexWalkerError
from pylatexenc.latex2text import LatexNodes2Text
from twython import Twython
import maya
import requests
from wand.image import Image, Color
import imageio

postGif = True

botHandle = "@CMS_results"
feedDict = {}
feedDict['CMS_PAS_FEED'] = 'https://cds.cern.ch/rss?cc=CMS%20Physics%20Analysis%20Summaries'
feedDict['CMS_PAPER_FEED'] = 'https://cds.cern.ch/rss?cc=CMS%20Publication%20Drafts%20Final'
# TODO: make flexible for several RSS feeds

daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger()
# imageio.plugins.freeimage.download()


def read_feed(rss_url):
    """read the RSS feed and return dictionary"""
    feed = feedparser.parse(rss_url)
    return feed


def format_title(title):
    """format the publication title"""
    try:
        text_title = LatexNodes2Text().latex_to_text(title)
    except LatexWalkerError as identifier:
        logger.error(identifier)
        text_title = title
    return text_title


def execute_command(command):
    """execute shell command using subprocess..."""
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
    result = ""
    exit_code = proc.wait()
    if exit_code != 0:
        for line in proc.stderr:
            result = result + line
        logger.error(result)
    else:
        for line in proc.stdout:
            result = result + line
        logger.debug(result)


def process_images(identifier, image_url_list, use_wand=True, use_imageio=True):
    """Download all images, store in directory, convert to png."""
    image_list = []
    images_for_gif = []
    if not os.path.exists(identifier):
        os.makedirs(identifier)
    max_dim = [0, 0]
    for image_url in image_url_list:
        # download images
        out_path = "{}/{}".format(identifier, image_url.rsplit("/", 1)[1])
        request = requests.get(image_url, stream=True)
        if request.status_code == 200:
            with open(out_path, 'wb') as file_handler:
                request.raw.decode_content = True
                shutil.copyfileobj(request.raw, file_handler)

        # Resizing images and converting PDFs to PNG
        if use_wand:
            with Image(filename="{}[0]".format(out_path)) as img:  # , resolution=300
                # process pdfs here only, others seem to be far too big
                if out_path.endswith('pdf'):
                    img.format = 'png'
                    img.background_color = Color('white')
                    if (img.size[0] > 2000) or (img.size[1] > 2000):
                        img.resize(int(img.size[0]*.5), int(img.size[1]*.5))
                    img.compression_quality = 75
                    filename = out_path
                    img.alpha_channel = 'remove'
                    img.trim()
                    filename = filename.replace(".pdf", ".png")
                    # save image in list
                    image_list.append(filename)
                    img.save(filename=filename)
                    # need to save max dimensions for gif canvas
                    for i in range(len(max_dim)):
                        if img.size[i] > max_dim[i]:
                            max_dim[i] = img.size[i]
            with Image(filename="{}[0]".format(out_path)) as img:
                if not out_path.endswith('pdf'):
                    img.format = 'png'
                    img.background_color = Color('white')
                    img.compression_quality = 75
                    # resize to maximally the size of the converted PDFs
                    side_to_scale = max(img.size[0], img.size[1])
                    scale_factor = max(max_dim[0], max_dim[1])/float(side_to_scale)
                    if scale_factor < 1:
                        img.resize(int(img.size[0]*scale_factor), int(img.size[1]*scale_factor))
                    # give the file a different name
                    filesplit = filename.rsplit(".", 1)
                    filename = filesplit[0] + "_." + filesplit[1]
                    # save image in list
                    image_list.append(filename)
                    img.save(filename=filename)
        else:
            command = "convert -quality 75% -trim"  # trim to get rid of whitespace
            with Image(filename="{}[0]".format(out_path)) as img:  # , resolution=300
                if (img.size[0] > 2000) or (img.size[1] > 2000):
                    command += " -resize 50%"
                filename = out_path.replace(".pdf", ".png")
                command += "%s %s" % (out_path, filename)
                execute_command(command)
    # bring list in order again
    image_list = sorted(image_list)
    if postGif:
        # now we need another loop to create the gif canvas
        for out_path in image_list:
            with Image(filename=out_path) as foreground:
                # foreground.transform(resize="{0}x{1}".format(*max_dim))
                with Image(width=max_dim[0], height=max_dim[1], background=Color('white')) as out:
                    left = int((max_dim[0] - foreground.size[0]) / 2)
                    top = int((max_dim[1] - foreground.size[1]) / 2)
                    out.composite(foreground, left=left, top=top)
                    out.save(filename=out_path)
            if use_imageio:
                images_for_gif.append(imageio.imread(out_path))
            else:
                images_for_gif.append(out_path)
        if use_imageio:
            imageio.mimsave('{id}/{id}.gif'.format(id=identifier), images_for_gif,
                            format='GIF-FI', duration=2, quantizer='nq', palettesize=255)
        else:
            command = "convert -delay 200 -loop 0 "
            command += " ".join(images_for_gif)
            command += ' {id}/{id}.gif'.format(id=identifier)
            execute_command(command)
        image_list.append('{id}/{id}.gif'.format(id=identifier))
    return image_list


def twitter_auth():
    """Authenticate to twitter."""
    from auth import (
        CONSUMER_KEY,
        CONSUMER_SECRET,
        ACCESS_TOKEN,
        ACCESS_TOKEN_SECRET
    )
    twitter = Twython(
        CONSUMER_KEY,
        CONSUMER_SECRET,
        ACCESS_TOKEN,
        ACCESS_TOKEN_SECRET
    )
    return twitter


def upload_images(twitter, image_list):
    """Upload images to twitter and return locations."""
    image_ids = []
    # loop over sorted images to get the plots in the right order
    for image_path in sorted(image_list):
        with open(image_path, 'rb') as image:
            response = None
            if postGif:
                if image_path.endswith("gif"):
                    response = twitter.upload_media(media=image, media_category="tweet_gif")
                    logger.debug(response)
                    image_ids.append(response["media_id"])
            else:
                response = twitter.upload_media(media=image)
                logger.debug(response)
                image_ids.append(response["media_id"])
    logger.debug(image_ids)
    return image_ids


def split_text(identifier, title, link, short_url_length, maxlength):
    """Split tweet into several including URL in first one"""
    message_list = []
    remaining_text = "{}: {}".format(identifier, title)
    first_message = True
    while len(remaining_text) > 0:
        message = remaining_text.lstrip()
        allowed_length = short_url_length
        if first_message:
            allowed_length = maxlength
        else:
            message = ".."+message
        if len(message) > allowed_length:
            # strip message at last whitespace and account for 3 dots
            cut_position = message[:allowed_length-3].rfind(" ")
            message = message[:cut_position]
            remaining_text = remaining_text[cut_position:]
            if cut_position+3 > len(remaining_text):
                message = message.strip()+".."
        else:
            remaining_text = ""
        if first_message:
            message = "{} {}".format(message, link)
            first_message = False
        else:
            message = botHandle + " + message
        message_list.append(message)
    return message_list


def tweet(twitter, identifier, title, link, image_ids):
    """tweet the new results with title and link and pictures taking care of length limitations."""
    # https://dev.twitter.com/rest/reference/get/help/configuration
    tweet_length = 140
    short_url_length = len(link)  # twitter.get_twitter_configuration()['short_url_length']
    maxlength = tweet_length - short_url_length

    message_list = split_text(identifier, title, link, tweet_length, maxlength)
    first_message = True
    previous_status_id = None
    response = {}
    for i, message in enumerate(message_list):
        logger.info(message)
        logger.debug(len(message))
        if "id" in response:
            previous_status_id = response["id"]
        if postGif:
            if first_message:
                response = twitter.update_status(status=message, media_ids=image_ids)
                first_message = False
                logger.debug(response)
            else:
                response = twitter.update_status(status=message, in_reply_to_status_id=previous_status_id)
                logger.debug(response)
        else:
            response = twitter.update_status(status=message, media_ids=image_ids[i*4:(i+1)*4], in_reply_to_status_id=previous_status_id)
            logger.debug(response)


def check_id_exists(identifier, feedId):
    """Check with ID of the analysis already exists in text file to avoid tweeting again."""
    txt_file_name = "%s.txt" % feedId
    # create file if it doesn't exist yet
    if not os.path.isfile(txt_file_name):
        open(txt_file_name, 'a').close()
    with open(txt_file_name) as txt_file:
        for line in txt_file:
            if (identifier == line.strip("\n")):
                return True
    return False


def store_id(identifier, feedId):
    """Store ID of the analysis in text file to avoid tweeting again."""
    txt_file_name = "%s.txt" % feedId
    with open(txt_file_name, 'a') as txt_file:
        txt_file.write("%s\n" % identifier)


def main():
    """Main function."""
    feedId = 'CMS_PAS_FEED'
    feed = read_feed(feedDict[feedId])
    twitter = twitter_auth()
    # loop over posts sorted by date
    for post in sorted(feed["entries"], key=lambda x: maya.parse(x["published"]).datetime()):
        image_url_list = []
        # logger.debug(post)
        identifier = post["dc_source"]
        if check_id_exists(identifier, feedId):
            logger.info("%s has already been tweeted for feed %s" % (identifier, feedId))
            continue
        logger.info("{id} - published: {date}".format(id=identifier, date=maya.parse(post["published"]).datetime()))
        # if post is already in the database, skip it
        thumbnail_url = None
        image_ids = None
        for thumbnail in post["media_thumbnail"]:
            thumbnail_found = True
            thumbnail_url = thumbnail["url"]
            thumbnail_url = thumbnail_url.split("?", 1)[0].replace("png", "pdf")
            logger.debug("thumbnail: " + thumbnail_url)
            request = requests.get(thumbnail_url)
            if not request.status_code < 400:
                # try to download png then
                thumbnail_url = thumbnail_url.replace("pdf", "png")
                request = requests.get(thumbnail_url)
                if not request.status_code < 400:
                    logger.error("thumbnail: " + thumbnail_url + " does not exist!")
                    thumbnail_found = False
            if thumbnail_found:
                image_url_list.append(thumbnail_url)
        image_list = process_images(identifier, image_url_list)
        image_ids = upload_images(twitter, image_list)
        # clean up images
        shutil.rmtree(identifier)

        title = post.title
        link = post.link
        title_formatted = format_title(title)
        if sys.version_info[0] < 3:
            title_formatted = title_formatted.encode('utf8')
        logger.info("{}: {} {}".format(identifier, title_formatted, link))
        tweet(twitter, identifier, title_formatted, link, image_ids)
        store_id(identifier, feedId)
        return


if __name__ == '__main__':
    main()
