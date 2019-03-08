"""Twitter bot to post latest CMS results."""
from __future__ import print_function
import os
import sys
import argparse
import shutil
import logging
import subprocess
import re
import configparser
import daiquiri
import feedparser
from io import BytesIO
from pylatexenc.latexwalker import LatexWalkerError
from pylatexenc.latex2text import LatexNodes2Text
from twython import Twython, TwythonError
import maya
import requests
from wand.image import Image, Color
from wand.exceptions import CorruptImageError
import imageio


# Maximum image dimension (both x and y)
MAX_IMG_DIM = 1200
MAX_IMG_SIZE = 5242880
# TODO: tag actual experiment?
# TODO: add some general tags?
# TODO: Make certain keywords tags
# collection could be: Higgs, NewPhysics, 13TeV/8TeV, StandardModel,
# resonances, DarkMatter, SUSY, BSM
# Also: CMSB2G, CMSHIG, CMSEXO etc.
# TopQuark, BottomQuark Quark/Quarks, Tau
CADI_TO_HASHTAG = {}
CADI_TO_HASHTAG['TOP'] = "#TopQuark"
CADI_TO_HASHTAG['HIG'] = "#HiggsBoson"
CADI_TO_HASHTAG['B2G'] = "#NewPhysics"
CADI_TO_HASHTAG['EXO'] = "#NewPhysics"
CADI_TO_HASHTAG['SUS'] = "#SuperSymmetry"
CADI_TO_HASHTAG['FTR'] = "#Upgrade"
CADI_TO_HASHTAG['SMP'] = "#StandardModel"
CADI_TO_HASHTAG['BPH'] = "#BPhysics"

# identifiers for preliminary results
PRELIM = ["CMS-PAS", "ATLAS-CONF"]


class Conference(object):
    __slots__ = ['name', 'start', 'end']

    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end

    def isNow(self, pub_date):
        if self.start <= maya.parse(pub_date) <= self.end:
            return f"#{self.name}{maya.now().year}"
        return ""


CONFERENCES = []
CONFERENCES.append(Conference("Moriond", maya.parse(
    f'{maya.now().year}-03-01'), maya.parse(f'{maya.now().year}-03-30')))


daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger()
# imageio.plugins.freeimage.download()


def read_feed(rss_url):
    """read the RSS feed and return dictionary"""
    try:
        response = requests.get(rss_url, timeout=10)
    except requests.ReadTimeout:
        logger.error("Timeout when reading RSS %s", rss_url)
        return
    # Turn stream into memory stream object for universal feedparser
    content = BytesIO(response.content)
    # Parse content
    feed = feedparser.parse(content)
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
    logger.debug(text_title)
    # insert spaces before and after the following characters
    char_with_spaces = ["=", "→"]
    for my_char in char_with_spaces:
        pat = re.compile(r"\s?%s\s?" % my_char)
        text_title = re.sub(pat, " %s " % my_char, text_title)
    # reduce all spaces to a maximum of one
    text_title = re.sub(r"\s+", " ", text_title)
    return text_title


def execute_command(command):
    """execute shell command using subprocess..."""
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True, universal_newlines=True)
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


def process_images(identifier, downloaded_image_list, post_gif, use_wand=True, use_imageio=True):
    """Convert/resize all images to png."""
    logger.info("Processing %d images." % len(downloaded_image_list))
    logger.debug("process_images(): identifier = {}, downloaded_image_list = {},\
                  use_wand = {}, use_imageio = {}".format(
        identifier, downloaded_image_list, use_wand, use_imageio))
    image_list = []
    images_for_gif = []
    max_dim = [0, 0]
    new_image_format = 'png'
    # also calculate average dimensions to scale down very large images
    dim_list_x = []
    dim_list_y = []

    # first loop to find maximum PDF dimensions to have high quality images
    for image_file in downloaded_image_list:
        if use_wand:
            # , resolution=300
            try:
                with Image(filename="{}[0]".format(image_file)) as img:
                    # process pdfs here only, others seem to be far too big
                    img.format = new_image_format
                    img.background_color = Color('white')
                    img.compression_quality = 75
                    filename = image_file
                    img.alpha_channel = 'remove'
                    img.trim(fuzz=0.01)
                    img.reset_coords()  # equivalent of repage
                    # give the file a different name
                    filesplit = image_file.rsplit(".", 1)
                    filename = filesplit[0] + "_." + filesplit[1]
                    if filename.endswith('pdf'):
                        filename = filename.replace(
                            ".pdf", ".%s" % new_image_format)
                    # save image in list
                    image_list.append(filename)
                    img.save(filename=filename)
                    dim_list_x.append(img.size[0])
                    dim_list_y.append(img.size[1])
                    # need to save max dimensions for gif canvas
                    for i, _ in enumerate(max_dim):
                        if img.size[i] > max_dim[i]:
                            max_dim[i] = img.size[i]
            except CorruptImageError as corrupt_except:
                print(corrupt_except)
                print("Ignoring", image_file)
    # rescale images
    average_dims = (float(sum(dim_list_x))/max(len(dim_list_x), 1),
                    float(sum(dim_list_y))/max(len(dim_list_y), 1))
    dim_xy = int(max(min(MAX_IMG_DIM, average_dims[0]), min(
        MAX_IMG_DIM, average_dims[0])))

    # print(max_dim[0], max_dim[1], dim_xy, MAX_IMG_DIM)
    # reset max_dim again
    max_dim = [0, 0]
    # scale individual images
    for image_file in image_list:
        if use_wand:
            filename = image_file
            with Image(filename=filename) as img:
                # print(filename, img.size[0], img.size[1])
                if (img.size[0] > dim_xy) or (img.size[1] > dim_xy):
                    scale_factor = dim_xy / \
                        float(max(img.size[0], img.size[1]))
                    img.resize(int(img.size[0] * scale_factor),
                               int(img.size[1] * scale_factor))
                for i, _ in enumerate(max_dim):
                    if img.size[i] > max_dim[i]:
                        max_dim[i] = img.size[i]
                img.save(filename=filename)

    # for image_file in downloaded_image_list:
    #     if use_wand:
    #         # already processed non-PDF files with wand
    #         if not image_file.endswith('pdf'):
    #             with Image(filename="{}[0]".format(image_file)) as img:
    #                 img.format = new_image_format
    #                 img.background_color = Color('white')
    #                 img.compression_quality = 75
    #                 img.alpha_channel = 'remove'
    #                 img.trim(fuzz=0.01)
    #                 img.reset_coords()  # same as repage
    #                 # resize to maximally the size of the converted PDFs
    #                 logger.debug("img.size[0] = {}, img.size[1] = {}".format(img.size[0],
    #                                                                          img.size[1]))
    #                 side_to_scale = max(img.size[0], img.size[1])
    #                 scale_factor = max(max_dim[0], max_dim[
    #                                    1]) / float(side_to_scale)
    #                 if scale_factor < 1:
    #                     img.resize(
    #                         int(img.size[0] * scale_factor), int(img.size[1] * scale_factor))
    #                 # give the file a different name
    #                 filesplit = image_file.rsplit(".", 1)
    #                 filename = filesplit[0] + "_." + filesplit[1]
    #                 # save image in list
    #                 image_list.append(filename)
    #                 img.save(filename=filename)
    #     else:
    #         # if using convert, no special treatment at the moment
    #         command = "convert -quality 75% -trim"  # trim to get rid of whitespace
    #         with Image(filename="{}[0]".format(image_file)) as img:  # , resolution=300
    #             if (img.size[0] > MAX_IMG_DIM) or (img.size[1] > MAX_IMG_DIM):
    #                 scale_factor = 100 * MAX_IMG_DIM / \
    #                     float(max(img.size[0], img.size[1]))
    #                 command += " -resize {}%".format(int(scale_factor))
    #             filename = image_file.replace(".pdf", ".%s" % new_image_format)
    #             command += "%s %s" % (image_file, filename)
    #             execute_command(command)

    # bring list in order again
    image_list = sorted(image_list)
    if post_gif:
        # now we need another loop to create the gif canvas
        for image_file in image_list:
            with Image(filename=image_file) as foreground:
                foreground.format = 'gif'
                image_file = image_file.replace(
                    '.%s' % new_image_format, '.gif')
                # foreground.transform(resize="{0}x{1}".format(*max_dim))
                add_margin = 1.03
                with Image(width=int(max_dim[0]*add_margin), height=int(max_dim[1]*add_margin),
                           background=Color('white')) as out:
                    left = int(
                        (max_dim[0]*add_margin - foreground.size[0]) / 2)
                    top = int((max_dim[1]*add_margin - foreground.size[1]) / 2)
                    out.composite(foreground, left=left, top=top)
                    out.save(filename=image_file)
            if use_imageio:
                images_for_gif.append(imageio.imread(image_file))
            else:
                images_for_gif.append(image_file)
        img_size = MAX_IMG_SIZE+1
        # the gif can only have a certain size, so we loop until it's small enough
        while img_size > MAX_IMG_SIZE:
            if use_imageio:
                imageio.mimsave('{id}/{id}.gif'.format(id=identifier), images_for_gif,
                                format='GIF-FI', duration=1.2, quantizer='nq', palettesize=256)
            else:
                command = "convert -delay 120 -loop 0 "
                # command = "gifsicle --delay=120 --loop "
                command += " ".join(images_for_gif)
                command += ' {id}/{id}.gif'.format(id=identifier)
                # command += ' > {id}/{id}.gif'.format(id=identifier)
                execute_command(command)
            img_size = os.path.getsize('{id}/{id}.gif'.format(id=identifier))
            if img_size > MAX_IMG_SIZE:
                images_for_gif = images_for_gif[:-1]
                logger.info("Image to big ({} bytes), dropping last figure, {} images in GIF".format(
                    img_size, len(images_for_gif)))
                # os.remove('{id}/{id}.gif'.format(id=identifier))
            # replace image list by GIF only
        image_list = ['{id}/{id}.gif'.format(id=identifier)]
    return image_list


def twitter_auth(auth_dict):
    """Authenticate to twitter."""
    try:
        twitter = Twython(
            auth_dict['CONSUMER_KEY'],
            auth_dict['CONSUMER_SECRET'],
            auth_dict['ACCESS_TOKEN'],
            auth_dict['ACCESS_TOKEN_SECRET']
        )
    except TwythonError as twython_error:
        print(twython_error)
        logger.error(twitter)
        sys.exit(1)
    return twitter


def load_config(experiment, feed_file, auth_file):
    # load configs into dict
    config_dict = {}
    config = configparser.RawConfigParser()
    # load the feed config
    config.read(feed_file)
    if experiment not in config.sections():
        logger.error("Experiment {} not found in {}".format(
            experiment, feed_file))
    config_dict["FEED_DICT"] = {}
    for key in config[experiment]:
        config_dict["FEED_DICT"][key.upper()] = config[experiment][key]
    # now load the secrets
    config.clear()
    config.read(auth_file)
    if experiment not in config.sections():
        logger.error("Experiment {} not found in {}".format(
            experiment, auth_file))
    config_dict["AUTH"] = {}
    for key in config[experiment]:
        config_dict["AUTH"][key.upper()] = config[experiment][key]
    return config_dict


def upload_images(twitter, image_list, post_gif):
    """Upload images to twitter and return locations."""
    logger.info("Uploading images.")
    image_ids = []
    # loop over sorted images to get the plots in the right order
    for image_path in sorted(image_list):
        with open(image_path, 'rb') as image:
            response = None
            if post_gif:
                if image_path.endswith("gif"):
                    try:
                        # while media_category="tweet_gif" should be used, this breaks the gif...
                        # response = twitter.upload_media(media=image,
                        # media_category="tweet_gif")
                        response = twitter.upload_media(media=image)
                    except TwythonError as twython_error:
                        print(twython_error)
                        logger.error(response)
                        sys.exit(1)
                    logger.info(response)
                    image_ids.append(response["media_id"])
            else:
                try:
                    response = twitter.upload_media(media=image)
                except TwythonError as twython_error:
                    print(twython_error)
                    logger.error(response)
                    sys.exit(1)
                logger.debug(response)
                image_ids.append(response["media_id"])
    logger.debug(image_ids)
    return image_ids


def split_text(identifier, title, hashtags_link, short_url_length, maxlength, bot_handle):
    """Split tweet into several including hashtags and URL in first one"""
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
            message = ".." + message
        if len(message) > allowed_length:
            # strip message at last whitespace and account for 3 dots
            cut_position = message[:allowed_length - 3].rfind(" ")
            message = message[:cut_position]
            remaining_text = remaining_text[cut_position:]
            if cut_position + 3 > len(remaining_text):
                message = message.strip() + ".."
        else:
            remaining_text = ""
        if first_message:
            message = "{} {}".format(message, hashtags_link)
            first_message = False
        else:
            message = bot_handle + " " + message
        message_list.append(message)
    return message_list


def tweet(twitter, identifier, title, link, conf_hashtags, image_ids, post_gif, bot_handle):
    """tweet the new results with title and link and pictures taking care of length limitations."""
    logger.info("Creating tweet.")
    # https://dev.twitter.com/rest/reference/get/help/configuration
    tweet_length = 280
    # twitter.get_twitter_configuration()['short_url_length']
    short_url_length = len(link)
    hashtags_link = link
    if conf_hashtags:
        hashtags_link = f"{conf_hashtags} {link}"
        short_url_length = len(hashtags_link)
    maxlength = tweet_length - short_url_length

    message_list = split_text(identifier, title, hashtags_link,
                              tweet_length, maxlength, bot_handle)
    first_message = True
    previous_status_id = None
    response = {}
    for i, message in enumerate(message_list):
        logger.info(message)
        logger.debug(len(message))
        if "id" in response:
            previous_status_id = response["id"]
        if post_gif:
            if first_message:
                try:
                    response = twitter.update_status(
                        status=message, media_ids=image_ids)
                except TwythonError as twython_error:
                    print(twython_error)
                    logger.error(response)
                    sys.exit(1)
                first_message = False
                logger.debug(response)
            else:
                try:
                    response = twitter.update_status(status=message,
                                                     in_reply_to_status_id=previous_status_id)
                except TwythonError as twython_error:
                    print(twython_error)
                    logger.error(response)
                    return None
                logger.debug(response)
        else:
            try:
                response = twitter.update_status(status=message,
                                                 media_ids=image_ids[
                                                     i * 4:(i + 1) * 4],
                                                 in_reply_to_status_id=previous_status_id)
            except TwythonError as twython_error:
                print(twython_error)
                logger.error(response)
                return None
            logger.debug(response)
    return response


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
    dry_run = False  # run without tweeting
    analysis_id = ""
    keep_image_dir = False
    list_analyses = False
    post_gif = True

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dry", help="perform dry run without tweeting",
                        action="store_true")
    parser.add_argument("-a", "--analysis", help="tweet specific analysis",
                        type=str)
    parser.add_argument("-m", "--max", help="maximum number of analyses to tweet",
                        type=int, default=3)
    parser.add_argument("-k", "--keep", help="keep image directory",
                        action="store_true")
    parser.add_argument("-l", "--list", help="list analyses for feeds, then quit",
                        action="store_true")
    parser.add_argument("-g", "--nogif", help="do not create GIF",
                        action="store_true")
    parser.add_argument("-e", "--experiment", help="experiment to tweet for",
                        type=str, default="CMS")
    parser.add_argument("-c", "--config", help="name of feeds config file",
                        type=str, default="feeds.ini")
    parser.add_argument("--auth", help="name of auth config file",
                        type=str, default="auth.ini")
    args = parser.parse_args()
    max_tweets = args.max
    if args.dry:
        dry_run = True
    if args.keep:
        keep_image_dir = True
    if args.list:
        list_analyses = True
    if args.nogif:
        post_gif = False
    if args.analysis:
        analysis_id = args.analysis
        max_tweets = 1
        logger.info("Looking for analysis with ID %s" % analysis_id)
    experiment = args.experiment
    feed_file = args.config
    auth_file = args.auth

    config = load_config(experiment, feed_file, auth_file)

    feed_entries = []
    for key in config['FEED_DICT']:
        logger.info(f"Getting feed for {key}")
        this_feed = read_feed(config['FEED_DICT'][key])
        if this_feed:
            this_feed_entries = this_feed["entries"]
            logger.info("Found %d items" % len(this_feed_entries))
            # add feed info to entries so that we can loop more easily later
            for index, _ in enumerate(this_feed_entries):
                this_feed_entries[index]["feed_id"] = key
            feed_entries += this_feed_entries
        else:
            logger.warning(f"Found no items for feed {key}")
    if list_analyses:
        # sort by feed_id, then date
        logger.info("List of available analyses:")
        for post in sorted(feed_entries,
                           key=lambda x: (x["feed_id"], maya.parse(x["published"]).datetime())):
            logger.info(" - {post_id} ({feed_id}), published {date}".format(
                post_id=post["dc_source"], feed_id=post["feed_id"], date=post["published"]))
        return
    twitter = twitter_auth(config['AUTH'])
    # loop over posts sorted by date
    tweet_count = 0
    for post in sorted(feed_entries, key=lambda x: maya.parse(x["published"]).datetime()):
        downloaded_image_list = []
        logger.debug(post)
        identifier = post["dc_source"]
        if analysis_id:
            if analysis_id not in identifier:
                continue
            else:
                logger.info("Found %s in feed %s" %
                            (identifier, post["feed_id"]))
        elif check_id_exists(identifier, post["feed_id"]):
            logger.debug("%s has already been tweeted for feed %s" %
                         (identifier, post["feed_id"]))
            continue
        tweet_count += 1
        logger.info("{id} - published: {date}".format(id=identifier,
                                                      date=maya.parse(post["published"]).datetime()))
        # if post is already in the database, skip it
        media_content = []
        arxiv_id = ""
        if "media_content" in post:
            media_content += post["media_content"]
        outdir = identifier.replace(':', '_')
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        for media in media_content:
            media_url = media["url"]
            # try to find arXiv ID
            if "files/arXiv:" in media_url:
                arxiv_id = media_url.rsplit("files/", 1)[1].strip(".pdf")
                continue
            # consider only attached Figures
            if experiment == "CMS":
                # CMS follows a certain standard
                # but figures can be both PDF and PNG
                if not re.search(r"/files\/.*[Ff]igures?_", media_url):
                    continue
            elif experiment == "ATLAS":
                # ATLAS seems to only use PNG format for plots
                if not media_url.lower().endswith(".png"):
                    continue
            media_found = True
            media_url = media_url.split("?", 1)[0]
            logger.debug("media: " + media_url)
            request = requests.get(media_url, timeout=10)
            if not request.status_code < 400:
                logger.error("media: " + media_url + " does not exist!")
                media_found = False

            if media_found:
                # download images
                out_path = "{}/{}".format(outdir,
                                          media_url.rsplit("/", 1)[1])
                request = requests.get(media_url, stream=True)
                if request.status_code == 200:
                    with open(out_path, 'wb') as file_handler:
                        request.raw.decode_content = True
                        shutil.copyfileobj(request.raw, file_handler)
                    if out_path.find("%") >= 0:
                        continue
                    downloaded_image_list.append(out_path)
        image_ids = []
        if downloaded_image_list:
            image_list = process_images(
                outdir, downloaded_image_list, post_gif)
            image_ids = upload_images(twitter, image_list, post_gif)

        title = post.title
        link = post.link
        # if arxiv_id:
        #     arxiv_link = "https://arxiv.org/abs/%s" % arxiv_id.rsplit(":")[1]
        #     logger.debug(arxiv_link)
        #     request = requests.get(arxiv_link)
        #     if request.status_code < 400:
        #         link = arxiv_link

        prelim_result = False
        for item in PRELIM:
            if identifier.find(item) >= 0:
                prelim_result = True
                logger.info("This is a preliminary result.")
        conf_hashtags = ""
        # use only for PAS/CONF notes:
        if prelim_result:
            conf_hashtags = " ".join(conf.isNow(
                post["published"]) for conf in CONFERENCES)
            logger.info(f"Conference hashtags: {conf_hashtags}")
        title_formatted = format_title(title)
        if sys.version_info[0] < 3:
            title_formatted = title_formatted.encode('utf8')
        logger.info("{}: {} {}".format(
            identifier, title_formatted, " ".join([conf_hashtags, link])))
        if not dry_run:
            tweet_response = tweet(twitter, identifier, title_formatted, link,
                                   image_ids, post_gif, config['AUTH']['BOT_HANDLE'])
            if not tweet_response:
                # try to recover since something went wrong
                # first, try to use individual images instead of GIF
                if post_gif:
                    if downloaded_image_list:
                        logger.info("Trying to tweet without GIF")
                        image_list = process_images(
                            outdir, downloaded_image_list, post_gif=False)
                        image_ids = upload_images(
                            twitter, image_list, post_gif=False)
                        tweet_response = tweet(
                            twitter, identifier, title_formatted, link, image_ids, post_gif=False,
                            bot_handle=config['AUTH']['BOT_HANDLE'])
            if not tweet_response:
                # second, try to tweet without image
                logger.info("Trying to tweet without images")
                tweet_response = tweet(
                    twitter, identifier, title_formatted, link, image_ids=[],
                    post_gif=False, bot_handle=config['AUTH']['BOT_HANDLE'])
            if tweet_response:
                store_id(identifier, post["feed_id"])
        if not keep_image_dir:
            # clean up images
            shutil.rmtree(outdir)
        if tweet_count >= max_tweets:
            return


if __name__ == '__main__':
    main()
