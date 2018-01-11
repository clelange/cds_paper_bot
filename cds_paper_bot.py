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
from twython import Twython, TwythonError
import maya
import requests
from wand.image import Image, Color
import imageio


postGif = True

botHandle = "@CMS_results"
feedDict = {}
feedDict['CMS_PAS_FEED'] = 'https://cds.cern.ch/rss?cc=CMS%20Physics%20Analysis%20Summaries'
feedDict['CMS_PAPER_FEED'] = 'https://cds.cern.ch/rss?cc=CMS%20Publication%20Drafts%20Final'
# Maximum image dimension (both x and y)
MAX_IMG_DIM = 2000
# Maximum number of tweets
MAX_TWEETS = 3
# TODO: tag actual experiment?
# TODO: add some general tags?
# TODO: Make certain keywords tags
# collection could be: Higgs, NewPhysics, 13TeV/8TeV, StandardModel, resonances, DarkMatter, SUSY, BSM
# Also: CMSB2G, CMSHIG, CMSEXO etc.
# TopQuark, BottomQuark Quark/Quarks, Tau

daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger()
# imageio.plugins.freeimage.download()


def read_feed(rss_url):
    """read the RSS feed and return dictionary"""
    feed = feedparser.parse(rss_url)
    return feed


def format_title(title):
    """format the publication title"""
    logger.info("Formatting title.")
    logger.info(title)
    try:
        text_title = LatexNodes2Text().latex_to_text(title)
    except LatexWalkerError as identifier:
        logger.error(identifier)
        text_title = title
    return text_title
    logger.info(text_title)


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


def process_images(identifier, downloaded_image_list, use_wand=True, use_imageio=True):
    """Convert/resize all images to png."""
    logger.info("Processing images.")
    logger.debug("process_images(): identifier = {}, downloaded_image_list = {},\
                  use_wand = {}, use_imageio = {}".format(
                      identifier, downloaded_image_list, use_wand, use_imageio))
    image_list = []
    images_for_gif = []
    max_dim = [0, 0]
    new_image_format = 'png'

    # first loop to find maximum PDF dimensions to have high quality images
    for image_file in downloaded_image_list:
        if image_file.endswith('pdf'):
            if use_wand:
                with Image(filename="{}[0]".format(image_file)) as img:  # , resolution=300
                    # process pdfs here only, others seem to be far too big
                    img.format = new_image_format
                    img.background_color = Color('white')
                    if (img.size[0] > MAX_IMG_DIM) or (img.size[1] > MAX_IMG_DIM):
                        img.resize(int(img.size[0]*.5), int(img.size[1]*.5))
                    img.compression_quality = 75
                    filename = image_file
                    img.alpha_channel = 'remove'
                    img.trim()
                    filename = filename.replace(".pdf", ".%s" % new_image_format)
                    # save image in list
                    image_list.append(filename)
                    img.save(filename=filename)
                    # need to save max dimensions for gif canvas
                    for i, _ in enumerate(max_dim):
                        if img.size[i] > max_dim[i]:
                            max_dim[i] = img.size[i]
    if (max(max_dim[0], max_dim[1]) == 0):
        for image_file in downloaded_image_list:
            if use_wand:
                with Image(filename="{}[0]".format(image_file)) as img:
                    if (img.size[0] > MAX_IMG_DIM) or (img.size[1] > MAX_IMG_DIM):
                        img.resize(int(img.size[0]*.5), int(img.size[1]*.5))
                    for i, _ in enumerate(max_dim):
                        if img.size[i] > max_dim[i]:
                            max_dim[i] = img.size[i]

    for image_file in downloaded_image_list:
        if use_wand:
            # already processed non-PDF files with wand
            if not image_file.endswith('pdf'):
                with Image(filename="{}[0]".format(image_file)) as img:
                    img.format = new_image_format
                    img.background_color = Color('white')
                    img.compression_quality = 75
                    # resize to maximally the size of the converted PDFs
                    logger.debug("img.size[0] = {}, img.size[1] = {}".format(img.size[0], img.size[1]))
                    side_to_scale = max(img.size[0], img.size[1])
                    scale_factor = max(max_dim[0], max_dim[1])/float(side_to_scale)
                    if scale_factor < 1:
                        img.resize(int(img.size[0]*scale_factor), int(img.size[1]*scale_factor))
                    # give the file a different name
                    filesplit = image_file.rsplit(".", 1)
                    filename = filesplit[0] + "_." + filesplit[1]
                    # save image in list
                    image_list.append(filename)
                    img.save(filename=filename)
        else:
            # if using convert, no special treatment at the moment
            command = "convert -quality 75% -trim"  # trim to get rid of whitespace
            with Image(filename="{}[0]".format(image_file)) as img:  # , resolution=300
                if (img.size[0] > MAX_IMG_DIM) or (img.size[1] > MAX_IMG_DIM):
                    command += " -resize 50%"
                filename = image_file.replace(".pdf", ".%s" % new_image_format)
                command += "%s %s" % (image_file, filename)
                execute_command(command)
    # bring list in order again
    image_list = sorted(image_list)
    if postGif:
        # now we need another loop to create the gif canvas
        for image_file in image_list:
            with Image(filename=image_file) as foreground:
                foreground.format = 'gif'
                image_file = image_file.replace('.%s' % new_image_format, '.gif')
                # foreground.transform(resize="{0}x{1}".format(*max_dim))
                with Image(width=max_dim[0], height=max_dim[1], background=Color('white')) as out:
                    left = int((max_dim[0] - foreground.size[0]) / 2)
                    top = int((max_dim[1] - foreground.size[1]) / 2)
                    out.composite(foreground, left=left, top=top)
                    out.save(filename=image_file)
            if use_imageio:
                images_for_gif.append(imageio.imread(image_file))
            else:
                images_for_gif.append(image_file)
        if use_imageio:
            imageio.mimsave('{id}/{id}.gif'.format(id=identifier), images_for_gif,
                            format='GIF-FI', duration=2, quantizer='nq', palettesize=256)
        else:
            command = "convert -delay 200 -loop 0 "
            # command = "gifsicle --delay=200 --loop "
            command += " ".join(images_for_gif)
            command += ' {id}/{id}.gif'.format(id=identifier)
            # command += ' > {id}/{id}.gif'.format(id=identifier)
            execute_command(command)
        # replace image list by GIF only
        image_list = ['{id}/{id}.gif'.format(id=identifier)]
    return image_list


def twitter_auth():
    """Authenticate to twitter."""
    from auth import (
        CONSUMER_KEY,
        CONSUMER_SECRET,
        ACCESS_TOKEN,
        ACCESS_TOKEN_SECRET
    )
    try:
        twitter = Twython(
            CONSUMER_KEY,
            CONSUMER_SECRET,
            ACCESS_TOKEN,
            ACCESS_TOKEN_SECRET
        )
    except TwythonError as twython_error:
        print(twython_error)
    return twitter


def upload_images(twitter, image_list):
    """Upload images to twitter and return locations."""
    logger.info("Uploading images.")
    image_ids = []
    # loop over sorted images to get the plots in the right order
    for image_path in sorted(image_list):
        with open(image_path, 'rb') as image:
            response = None
            if postGif:
                if image_path.endswith("gif"):
                    try:
                        # while media_category="tweet_gif" should be used, this breaks the gif...
                        # response = twitter.upload_media(media=image, media_category="tweet_gif")
                        response = twitter.upload_media(media=image)
                    except TwythonError as twython_error:
                        print(twython_error)
                    logger.info(response)
                    image_ids.append(response["media_id"])
            else:
                try:
                    response = twitter.upload_media(media=image)
                except TwythonError as twython_error:
                    print(twython_error)
                logger.debug(response)
                image_ids.append(response["media_id"])
    logger.debug(image_ids)
    return image_ids


def split_text(identifier, title, link, short_url_length, maxlength):
    """Split tweet into several including URL in first one"""
    logger.info("Splitting text.")
    message_list = []
    remaining_text = "{}: {}".format(identifier, title)
    first_message = True
    while remaining_text:
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
            message = botHandle + " " + message
        message_list.append(message)
    return message_list


def tweet(twitter, identifier, title, link, image_ids):
    """tweet the new results with title and link and pictures taking care of length limitations."""
    logger.info("Creating tweet.")
    # https://dev.twitter.com/rest/reference/get/help/configuration
    tweet_length = 280
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
                try:
                    response = twitter.update_status(status=message, media_ids=image_ids)
                except TwythonError as twython_error:
                    print(twython_error)
                first_message = False
                logger.debug(response)
            else:
                try:
                    response = twitter.update_status(status=message, in_reply_to_status_id=previous_status_id)
                except TwythonError as twython_error:
                    print(twython_error)
                logger.debug(response)
        else:
            try:
                response = twitter.update_status(status=message, media_ids=image_ids[i*4:(i+1)*4], in_reply_to_status_id=previous_status_id)
            except TwythonError as twython_error:
                print(twython_error)
            logger.debug(response)


def check_id_exists(identifier, feed_id):
    """Check with ID of the analysis already exists in text file to avoid tweeting again."""
    txt_file_name = "%s.txt" % feed_id
    # create file if it doesn't exist yet
    if not os.path.isfile(txt_file_name):
        open(txt_file_name, 'a').close()
    with open(txt_file_name) as txt_file:
        for line in txt_file:
            if identifier == line.strip("\n"):
                return True
    return False


def store_id(identifier, feed_id):
    """Store ID of the analysis in text file to avoid tweeting again."""
    txt_file_name = "%s.txt" % feed_id
    with open(txt_file_name, 'a') as txt_file:
        txt_file.write("%s\n" % identifier)


def main():
    """Main function."""
    feed_entries = []
    for key in feedDict:
        logger.info("Getting feed for %s" % key)
        this_feed = read_feed(feedDict[key])
        this_feed_entries = this_feed["entries"]
        logger.info("Found %d items" % len(this_feed_entries))
        # add feed info to entries so that we can loop more easily later
        for index, _ in enumerate(this_feed_entries):
            this_feed_entries[index]["feed_id"] = key
        feed_entries += this_feed_entries
    twitter = twitter_auth()
    # loop over posts sorted by date
    tweetCount = 0
    for post in sorted(feed_entries, key=lambda x: maya.parse(x["published"]).datetime()):
        downloaded_image_list = []
        logger.debug(post)
        identifier = post["dc_source"]
        if check_id_exists(identifier, post["feed_id"]):
            logger.info("%s has already been tweeted for feed %s" % (identifier, post["feed_id"]))
            continue
        tweetCount += 1
        logger.info("{id} - published: {date}".format(id=identifier, date=maya.parse(post["published"]).datetime()))
        # if post is already in the database, skip it
        media_content = []
        arXivId = ""
        if "media_content" in post:
            media_content += post["media_content"]
        if not os.path.exists(identifier):
            os.makedirs(identifier)
        for media in media_content:
            media_url = media["url"]
            # try to find arXiv ID
            if "files/arXiv:" in media_url:
                arXivId = media_url.rsplit("files/", 1)[1].strip(".pdf")
            # consider only attached Figures
            if "/files/Figure_" not in media_url:
                continue
            media_found = True
            media_url = media_url.split("?", 1)[0]
            logger.debug("media: " + media_url)
            request = requests.get(media_url)
            if not request.status_code < 400:
                logger.error("media: " + media_url + " does not exist!")
                media_found = False

            if media_found:
                # download images
                out_path = "{}/{}".format(identifier, media_url.rsplit("/", 1)[1])
                request = requests.get(media_url, stream=True)
                if request.status_code == 200:
                    with open(out_path, 'wb') as file_handler:
                        request.raw.decode_content = True
                        shutil.copyfileobj(request.raw, file_handler)
                    downloaded_image_list.append(out_path)
        image_list = process_images(identifier, downloaded_image_list)
        image_ids = upload_images(twitter, image_list)
        # clean up images
        shutil.rmtree(identifier)

        title = post.title
        link = post.link
        if arXivId:
            arXivLink = "https://arxiv.org/abs/%s" % arXivId.rsplit(":")[1]
            logger.debug(arXivLink)
            request = requests.get(arXivLink)
            if request.status_code < 400:
                link = arXivLink
        title_formatted = format_title(title)
        if sys.version_info[0] < 3:
            title_formatted = title_formatted.encode('utf8')
        logger.info("{}: {} {}".format(identifier, title_formatted, link))
        tweet(twitter, identifier, title_formatted, link, image_ids)
        store_id(identifier, post["feed_id"])
        if tweetCount >= MAX_TWEETS:
            return


if __name__ == '__main__':
    main()
