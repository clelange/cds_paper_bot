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
from io import BytesIO
from pathlib import Path
import zipfile
import daiquiri
import feedparser
import lxml.html as lh
from pylatexenc.latexwalker import LatexWalkerError
from pylatexenc.latex2text import LatexNodes2Text
import tweepy
import mastodon
import maya
import requests
import time
from wand.image import Image, Color
from wand.exceptions import CorruptImageError  # pylint: disable=no-name-in-module

# Assuming atproto is installed
from atproto import Client as BlueskyClient
from atproto import models as atproto_models
from atproto.exceptions import AtProtocolError as BlueskyAtpApiError

# Maximum image dimension (both x and y)
MAX_IMG_DIM = 1000  # could be 1280
MAX_IMG_DIM_AREA = 1280 * 720  # 1 megapixel
MAX_IMG_SIZE = 5242880
# TODO: tag actual experiment?
# TODO: Make certain keywords tags
# collection could be: Higgs, NewPhysics, 13TeV/8TeV, StandardModel,
# resonances, DarkMatter, SUSY, BSM
# Also: CMSB2G, CMSHIG, CMSEXO etc.
# TopQuark, BottomQuark Quark/Quarks, Tau
CADI_TO_HASHTAG = {}
CADI_TO_HASHTAG["TOP"] = "#TopQuark"
CADI_TO_HASHTAG["HIG"] = "#HiggsBoson"
CADI_TO_HASHTAG["B2G"] = "#NewPhysics"
CADI_TO_HASHTAG["EXO"] = "#NewPhysics"
CADI_TO_HASHTAG["SUS"] = "#SuperSymmetry"
CADI_TO_HASHTAG["FTR"] = "#Upgrade"
CADI_TO_HASHTAG["SMP"] = "#StandardModel"
CADI_TO_HASHTAG["BPH"] = "#BPhysics"
CADI_TO_HASHTAG["JME"] = "#Jets"
CADI_TO_HASHTAG["BTV"] = "#FlavourTagging"
CADI_TO_HASHTAG["MUO"] = "#Muons"
CADI_TO_HASHTAG["TAU"] = "#Taus #TauLeptons"
CADI_TO_HASHTAG["EGM"] = "#Electrons #Photons"
CADI_TO_HASHTAG["LUM"] = "#Luminosity"
CADI_TO_HASHTAG["PRF"] = "#ParticleFlow"
CADI_TO_HASHTAG["HIN"] = "#HeavyIons"

# identifiers for preliminary results
PRELIM = ["CMS-PAS", "ATLAS-CONF", "LHCb-CONF"]


class Conference(object):
    """Define conference class for hashtag implementation."""

    __slots__ = ["name", "start", "end"]

    def __init__(self, name, start, end):
        """Initialise with conf name, start and end dates."""
        self.name = name
        self.start = start
        self.end = end

    def is_now(self, pub_date):
        """Return conference name if publication date is within date range."""
        if self.start <= maya.parse(pub_date) <= self.end:
            # return f"#{self.name}{maya.now().year}"
            return f"#{self.name}"
        return ""


CONFERENCES = []
CONFERENCES.append(
    Conference(
        "Moriond",
        maya.parse(f"{maya.now().year}-03-23"),
        maya.parse(f"{maya.now().year}-04-11"),
    )
)
CONFERENCES.append(
    Conference(
        "EPSHEP2023 EPSHEP23", maya.parse("2023-08-20"), maya.parse("2023-08-30")
    )
)
CONFERENCES.append(
    Conference("LeptonPhoton23", maya.parse("2023-07-16"), maya.parse("2023-07-26"))
)
CONFERENCES.append(
    Conference("topq2023", maya.parse("2023-09-23"), maya.parse("2023-10-03"))
)
CONFERENCES.append(
    Conference("HiggsCouplings", maya.parse("2019-09-29"), maya.parse("2019-10-06"))
)
CONFERENCES.append(
    Conference("Higgs2023", maya.parse("2023-11-26"), maya.parse("2023-12-06"))
)
CONFERENCES.append(
    Conference("QM2023", maya.parse("2023-09-01"), maya.parse("2023-09-11"))
)
CONFERENCES.append(
    Conference("LHCP #LHCP2024", maya.parse("2024-06-01"), maya.parse("2024-06-10"))
)
CONFERENCES.append(
    Conference("ICHEP2024", maya.parse("2024-07-16"), maya.parse("2024-07-26"))
)
CONFERENCES.append(
    Conference("BOOST2024", maya.parse("2023-07-27"), maya.parse("2023-08-07"))
)

daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger()  # pylint: disable=invalid-name


def get_twitter_conn_v1(
    api_key, api_secret, access_token, access_token_secret
) -> tweepy.API:
    """Get twitter conn 1.1"""

    auth = tweepy.OAuth1UserHandler(api_key, api_secret)
    auth.set_access_token(
        access_token,
        access_token_secret,
    )
    return tweepy.API(auth)


def get_twitter_conn_v2(
    api_key, api_secret, access_token, access_token_secret
) -> tweepy.Client:
    """Get twitter conn 2.0"""

    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )

    return client


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


def read_html(html_url):
    """read the HTML page and return dictionary"""
    try:
        response = requests.get(html_url, timeout=10)
    except requests.ReadTimeout:
        logger.error("Timeout when reading HTML %s", html_url)
        return
    # Turn stream into memory stream object for universal feedparser
    content = BytesIO(response.content)
    # Parse content
    # html = lh.fromstring(content)
    html = lh.parse(content)
    return html


def convert_to_unicode(text):
    """Convert some standard sub- and superscripts to unicode."""
    # Check https://github.com/svenkreiss/unicodeit in the long run
    unicode_text = text
    unicode_text = unicode_text.replace("_S^0", "⁰_S ")
    unicode_text = unicode_text.replace("^0_S", "⁰_S ")
    # s quarks
    unicode_text = unicode_text.replace("_(s)^0", "⁰_s ")
    unicode_text = unicode_text.replace("^0_(s)", "⁰_s ")
    unicode_text = unicode_text.replace("_s^*±", "*^±_s ")
    unicode_text = unicode_text.replace("_s^0", "⁰_s ")
    unicode_text = unicode_text.replace("^0_s", "⁰_s ")
    unicode_text = unicode_text.replace("_s^+", "⁺_s ")
    unicode_text = unicode_text.replace("^+_s", "⁺_s ")
    unicode_text = unicode_text.replace("_s^-", "⁻_s ")
    unicode_text = unicode_text.replace("^-_s", "⁻_s ")
    unicode_text = unicode_text.replace("_s^±", "^±_s ")
    # b quarks
    unicode_text = unicode_text.replace("_b^*±", "*^±_b ")
    unicode_text = unicode_text.replace("_b^0", "⁰_b ")
    unicode_text = unicode_text.replace("^0_b", "⁰_b ")
    unicode_text = unicode_text.replace("_b^+", "⁺_b ")
    unicode_text = unicode_text.replace("^+_b", "⁺_b ")
    unicode_text = unicode_text.replace("_b^-", "⁻_b ")
    unicode_text = unicode_text.replace("^-_b", "⁻_b ")
    unicode_text = unicode_text.replace("_b^±", "^±_b ")
    # c quarks
    unicode_text = unicode_text.replace("_c^*±", "*^±_c ")
    unicode_text = unicode_text.replace("_c^0", "⁰_c ")
    unicode_text = unicode_text.replace("^0_c", "⁰_c ")
    unicode_text = unicode_text.replace("_c^+", "⁺_c ")
    unicode_text = unicode_text.replace("^+_c", "⁺_c ")
    unicode_text = unicode_text.replace("_c^-", "⁻_c ")
    unicode_text = unicode_text.replace("^-_c", "⁻_c ")
    unicode_text = unicode_text.replace("_c^±", "^±_c ")
    # more complicated combinations
    unicode_text = unicode_text.replace("_cc^+", "⁺_cc ")
    unicode_text = unicode_text.replace("(770)^0", "⁰(770)")
    unicode_text = unicode_text.replace("(892)^0", "⁰(892)")
    unicode_text = unicode_text.replace("_c(4312)^+", "⁺_c(4312)")
    unicode_text = unicode_text.replace("_c(4450)^+", "⁺_c(4450)")
    unicode_text = unicode_text.replace("^-1", "⁻¹")
    unicode_text = unicode_text.replace("^-2", "⁻²")
    unicode_text = unicode_text.replace("^∗+", "*⁺")
    unicode_text = unicode_text.replace("^+*", "⁺*")
    unicode_text = unicode_text.replace("^∗-", "*⁻")
    unicode_text = unicode_text.replace("^-*", "⁻*")
    unicode_text = unicode_text.replace("^∗0", "*⁰")
    unicode_text = unicode_text.replace("^0*", "⁰*")
    unicode_text = unicode_text.replace("^*0", "*⁰")
    unicode_text = unicode_text.replace("^*±", "*^±")
    unicode_text = unicode_text.replace("^++", "⁺⁺")
    unicode_text = unicode_text.replace("^+", "⁺")
    unicode_text = unicode_text.replace("^--", "⁻⁻")
    unicode_text = unicode_text.replace("^-", "⁻")
    unicode_text = unicode_text.replace("_-", "₊")
    unicode_text = unicode_text.replace("_-", "₋")
    unicode_text = unicode_text.replace("^0", "⁰")
    unicode_text = unicode_text.replace("_0", "₀")
    unicode_text = unicode_text.replace("^*", "*")
    # Remove parentheses for pp centre-of-mass energy
    unicode_text = unicode_text.replace("√(s)", "√s")
    return unicode_text


def format_title(title):
    """format the publication title"""
    logger.info("Formatting title.")
    logger.info(title)
    title = title.replace("\\sqrt s", "\\sqrt{s}")
    title = title.replace(" sqrts ", " \\sqrt{s} ")
    title = title.replace(" \\bar{", "\\bar{")
    title = title.replace("\\smash[b]", "")
    title = title.replace("\\smash [b]", "")
    title = title.replace("\\mbox{", "{")
    title = title.replace("{\\rm ", "{")
    title = title.replace("{\\rm\\scriptscriptstyle ", "{")
    title = title.replace("\\kern -0.1em ", "")
    title = title.replace("$~\\mathrm{", "~$\\mathrm{")
    if re.search(r"rightarrow\S", title):
        title = title.replace("rightarrow", "rightarrow ")
    # fix overline without space
    overline = re.search(r"overline\s([a-zA-Z])", title)
    if overline:
        title = title.replace(
            f"overline {overline.group(1)}", "overline{%s}" % overline.group(1)
        )
    title = title.replace(" \\overline{", "\\overline{")
    # overline{D} gives problems when in mathrm
    title = title.replace("\\overline{D", "\\bar{D")
    try:
        text_title = LatexNodes2Text().latex_to_text(title)
    except LatexWalkerError as identifier:
        logger.error(identifier)
        text_title = title
    logger.debug(text_title)
    # Convert some of remaining text to unicode
    text_title = convert_to_unicode(text_title)
    # insert spaces before and after the following characters
    char_with_spaces = ["=", "→"]
    for my_char in char_with_spaces:
        pat = re.compile(r"\s?%s\s?" % my_char)
        text_title = re.sub(pat, " %s " % my_char, text_title)
    # insert space before eV/keV/MeV/GeV/TeV in case of wrong formatting
    text_title = re.sub(r"(\d)([kMGT]?eV)", r"\1 \2", text_title)
    # reduce all spaces to a maximum of one
    text_title = re.sub(r"\s+", " ", text_title)
    # reduce all underscores to a maximum of one
    text_title = re.sub(r"_+", "_", text_title)
    # reduce all hyphens to a maximum of one
    text_title = re.sub(r"-+", "-", text_title)
    # remove space before comma
    text_title = text_title.replace(" ,", ",")
    # merge s_NN
    text_title = text_title.replace("s_ NN", "s_NN").strip()
    return text_title


def execute_command(command):
    """execute shell command using subprocess..."""
    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        universal_newlines=True,
    )
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


def process_images(identifier, downloaded_image_list, post_gif, use_wand=True):
    """Convert/resize all images to png."""
    logger.info("Processing %d images." % len(downloaded_image_list))
    logger.debug(
        "process_images(): identifier = {}, downloaded_image_list = {},\
                  use_wand = {}".format(identifier, downloaded_image_list, use_wand)
    )
    image_list = []
    images_for_gif = []
    max_dim = [0, 0]
    new_image_format = "png"
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
                    img.background_color = Color("white")
                    img.compression_quality = 85  # was 75
                    filename = image_file
                    img.alpha_channel = "remove"
                    img.trim(fuzz=0.01)
                    img.reset_coords()  # equivalent of repage
                    # give the file a different name
                    filesplit = image_file.rsplit(".", 1)
                    filename = filesplit[0] + "_." + filesplit[1]
                    if filename.endswith("pdf"):
                        filename = filename.replace(".pdf", ".%s" % new_image_format)
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
                logger.error(
                    f"CorruptImageError: {corrupt_except} for file {image_file}"
                )
                logger.warning(f"Ignoring {image_file} due to CorruptImageError.")
            except Exception as general_exception:  # pylint: disable=broad-except
                logger.error(
                    f"General exception processing image {image_file}: {general_exception}"
                )
    # rescale images
    average_dims = (
        float(sum(dim_list_x)) / max(len(dim_list_x), 1),
        float(sum(dim_list_y)) / max(len(dim_list_y), 1),
    )
    dim_xy = int(
        max(min(MAX_IMG_DIM, average_dims[0]), min(MAX_IMG_DIM, average_dims[0]))
    )

    # reset max_dim again
    max_dim = [0, 0]
    # scale individual images
    for image_file in image_list:
        if use_wand:
            filename = image_file
            with Image(filename=filename) as img:
                # logger.debug(f"Initial dimensions for {filename}: {img.size[0]}x{img.size[1]}")
                if (img.size[0] > dim_xy) or (img.size[1] > dim_xy):
                    scale_factor = dim_xy / float(max(img.size[0], img.size[1]))
                    area = scale_factor * scale_factor * img.size[0] * img.size[1]
                    logger.debug(
                        f"Scaling {filename}: dim_xy={dim_xy}, scale_factor={scale_factor:.2f}, area={area:.0f}, MAX_IMG_DIM_AREA={MAX_IMG_DIM_AREA}, original_size={img.size}"
                    )
                    if area > MAX_IMG_DIM_AREA:
                        scale_factor *= (
                            float(MAX_IMG_DIM_AREA / area) * 0.97
                        )  # factor 0.97 accounts for additional margin below
                    img.resize(
                        int(img.size[0] * scale_factor), int(img.size[1] * scale_factor)
                    )
                for i, _ in enumerate(max_dim):
                    if img.size[i] > max_dim[i]:
                        max_dim[i] = img.size[i]
                img.save(filename=filename)

    # bring list in order again
    image_list = sorted(image_list)
    if post_gif:
        # now we need another loop to create the gif canvas
        for image_file in image_list:
            with Image(filename=image_file) as foreground:
                foreground.format = "gif"
                image_file = image_file.replace(".%s" % new_image_format, ".gif")
                # foreground.transform(resize="{0}x{1}".format(*max_dim))
                add_margin = 1.03
                with Image(
                    width=int(max_dim[0] * add_margin),
                    height=int(max_dim[1] * add_margin),
                    background=Color("white"),
                ) as out:
                    left = int((max_dim[0] * add_margin - foreground.size[0]) / 2)
                    top = int((max_dim[1] * add_margin - foreground.size[1]) / 2)
                    out.composite(foreground, left=left, top=top)
                    out.save(filename=image_file)
            images_for_gif.append(image_file)
        img_size = MAX_IMG_SIZE + 1
        # the gif can only have a certain size, so we loop until it's small enough
        while img_size > MAX_IMG_SIZE:
            command = "convert -delay 200 -loop 0 "
            # command = "gifsicle --delay=120 --loop "
            command += " ".join(images_for_gif)
            command += " {id}/{id}.gif".format(id=identifier)
            # command += ' > {id}/{id}.gif'.format(id=identifier)
            execute_command(command)
            img_size = os.path.getsize("{id}/{id}.gif".format(id=identifier))
            if img_size > MAX_IMG_SIZE:
                images_for_gif = images_for_gif[:-1]
                logger.info(
                    "Image to big ({} bytes), dropping last figure, {} images in GIF".format(
                        img_size, len(images_for_gif)
                    )
                )
                # os.remove('{id}/{id}.gif'.format(id=identifier))
            # replace image list by GIF only
        image_list = ["{id}/{id}.gif".format(id=identifier)]
    return image_list


def twitter_auth(auth_dict):
    """Authenticate to twitter."""
    twitter_client_v1 = None
    twitter_client_v2 = None
    if "CONSUMER_KEY" not in auth_dict:
        return None
    try:
        twitter_client_v1 = get_twitter_conn_v1(
            api_key=auth_dict["CONSUMER_KEY"],
            api_secret=auth_dict["CONSUMER_SECRET"],
            access_token=auth_dict["ACCESS_TOKEN"],
            access_token_secret=auth_dict["ACCESS_TOKEN_SECRET"],
        )
        twitter_client_v2 = get_twitter_conn_v2(
            api_key=auth_dict["CONSUMER_KEY"],
            api_secret=auth_dict["CONSUMER_SECRET"],
            access_token=auth_dict["ACCESS_TOKEN"],
            access_token_secret=auth_dict["ACCESS_TOKEN_SECRET"],
        )
    except tweepy.TweepyException as tweepy_exception:
        logger.error(f"Twitter v1/v2 auth error: {tweepy_exception}")
        logger.error(f"Twitter client v1 state: {twitter_client_v1}")
        logger.error(f"Twitter client v2 state: {twitter_client_v2}")
        sys.exit(1)
    return {"v1": twitter_client_v1, "v2": twitter_client_v2}


def mastodon_auth(auth_dict):
    """Authenticate to mastodon."""
    mastodon_client = None
    if "MASTODON_ACCESS_TOKEN" not in auth_dict:
        return None
    # Extract api_base_url from MASTODON_HANDLE
    api_base_url = f"https://{auth_dict['MASTODON_BOT_HANDLE'].split('@')[-1]}/"
    logger.info(
        f"Using api_base_url: {api_base_url} for {auth_dict['MASTODON_BOT_HANDLE']}"
    )
    try:
        mastodon_client = mastodon.Mastodon(
            access_token=auth_dict["MASTODON_ACCESS_TOKEN"],
            api_base_url=api_base_url,
        )
    except Exception as mastodon_exception:  # pylint: disable=broad-except
        logger.error(f"Mastodon auth error: {mastodon_exception}")
        logger.error(f"Mastodon client state: {mastodon_client}")
        sys.exit(1)
    return mastodon_client


def bluesky_auth(auth_dict):
    """Authenticate to BlueSky."""
    # Assuming atproto is installed, so direct check for credentials.
    if "BLUESKY_HANDLE" not in auth_dict or "BLUESKY_APP_PASSWORD" not in auth_dict:
        logger.info(
            "BlueSky handle or app password not found in auth config. Skipping BlueSky."
        )
        return None

    bluesky_client = None
    try:
        bluesky_client = BlueskyClient()
        bluesky_client.login(
            auth_dict["BLUESKY_HANDLE"], auth_dict["BLUESKY_APP_PASSWORD"]
        )
        logger.info(
            f"Successfully logged into BlueSky as {auth_dict['BLUESKY_HANDLE']}"
        )
    except Exception as bluesky_exception:
        logger.error(f"BlueSky auth error: {bluesky_exception}")
        # We don't sys.exit here to allow other platforms to continue
        return None
    return bluesky_client


def load_config(experiment, feed_file, auth_file):
    """Load configs into dict."""
    config_dict = {}
    config = configparser.RawConfigParser()
    # load the feed config
    config.read(feed_file)
    if experiment not in config.sections():
        logger.error(f"Experiment {experiment} not found in {feed_file}")
    config_dict["FEED_DICT"] = {}
    for key in config[experiment]:
        config_dict["FEED_DICT"][key.upper()] = config[experiment][key]
    # now load the secrets
    config.clear()
    config.read(auth_file)
    if experiment not in config.sections():
        logger.error("Experiment {} not found in {}".format(experiment, auth_file))
    config_dict["AUTH"] = {}
    for key in config[experiment]:
        config_dict["AUTH"][key.upper()] = config[experiment][key]
    return config_dict


def twitter_upload_images(twitter, image_list, post_gif):
    """Upload images to twitter and return locations."""
    logger.info("Uploading images to Twitter.")
    image_ids = []
    # loop over sorted images to get the plots in the right order
    for image_path in sorted(image_list):
        response = None
        if post_gif:
            if image_path.endswith("gif"):
                try:
                    # while media_category="tweet_gif" should be used, this breaks the gif...
                    # response = twitter.media_upload(filename=image_path,
                    # media_category="tweet_gif")
                    response = twitter.media_upload(filename=image_path)
                except tweepy.TweepyException as tweepy_exception:
                    logger.error(
                        f"Twitter GIF upload error for {image_path}: {tweepy_exception}"
                    )
                    logger.error(f"Response state: {response}")
                    sys.exit(1)
                logger.info(response)
                image_ids.append(response.media_id)
        else:
            try:
                response = twitter.media_upload(filename=image_path)
            except tweepy.TweepyException as tweepy_exception:
                logger.error(
                    f"Twitter image upload error for {image_path}: {tweepy_exception}"
                )
                logger.error(f"Response state: {response}")
                sys.exit(1)
            logger.info(response)
            image_ids.append(response.media_id)
    logger.info(image_ids)
    return image_ids


def mastodon_upload_images(mastodon_client, image_list, post_gif):
    """Upload images to Mastodon and return locations."""
    logger.info("Uploading images to Mastodon.")
    image_ids = []
    # loop over sorted images to get the plots in the right order
    for image_path in sorted(image_list):
        if post_gif:
            if image_path.endswith("gif"):
                try:
                    response = mastodon_client.media_post(
                        media_file=image_path,
                        description=f"Animated GIF image for {image_path.split('/')[0]}",
                    )
                except mastodon.MastodonError as mastodon_exception:
                    logger.error(
                        f"Mastodon: Failed to upload media {image_path}. Error: {mastodon_exception}"
                    )
                    raise mastodon_exception
                logger.info(response)
                image_ids.append(response.id)
        else:
            try:
                response = mastodon_client.media_post(
                    media_file=image_path,
                    description=f"Image for {image_path.split('/')[0]}",
                )
            except mastodon.MastodonError as mastodon_exception:
                logger.error(
                    f"Mastodon: Failed to upload media {image_path}. Error: {mastodon_exception}"
                )
                raise mastodon_exception
            logger.info(response)
            image_ids.append(response.id)
    logger.info(image_ids)
    return image_ids


def bluesky_upload_images(bluesky_client, image_list, identifier_for_alt_text):
    """Upload images to BlueSky and return blob references."""
    if not bluesky_client or BlueskyClient is None or atproto_models is None:
        return []
    logger.info("Uploading images to BlueSky.")
    image_blobs = []
    # BlueSky allows up to 4 images
    for image_path in sorted(image_list)[:4]:
        try:
            with open(image_path, "rb") as f:
                img_data = f.read()

            alt_text_description = (
                f"Image for {identifier_for_alt_text}: {os.path.basename(image_path)}"
            )
            # Truncate alt text if too long
            max_alt_text_len = (
                500  # A reasonable guess, atproto might have stricter internal limits
            )
            if len(alt_text_description) > max_alt_text_len:
                alt_text_description = (
                    alt_text_description[: max_alt_text_len - 3] + "..."
                )

            response = bluesky_client.com.atproto.repo.upload_blob(img_data)
            image_blobs.append(
                atproto_models.AppBskyEmbedImages.Image(  # pyright: ignore [reportOptionalMemberAccess]
                    image=response.blob, alt=alt_text_description
                )
            )
            logger.info(
                f"BlueSky: Uploaded {image_path}, blob CID: {response.blob.cid}"
            )
        except Exception as e:
            logger.error(f"BlueSky: Failed to upload media {image_path}. Error: {e}")
            # Continue to try uploading other images if one fails
    logger.info(f"BlueSky uploaded blobs: {len(image_blobs)}")
    return image_blobs


def split_text(
    type_hashtag,
    title,
    identifier,
    link,
    conf_hashtags,
    phys_hashtags,
    post_length,
    bot_handle,
):
    """Split tweet into several including hashtags and URL in first one"""
    # type_hashtag: aaa bbb ccc .. link conf_hashtags
    # .. ddd eee (identifier)
    logger.info("Splitting text ...")
    message_list = []
    # add length+1 if value set
    length_link_and_tags = sum(
        (len(x) > 0) + len(x) for x in [link, conf_hashtags, phys_hashtags]
    )
    remaining_text = f"{type_hashtag}: {title} ({identifier})"
    first_message = True
    while remaining_text:
        message = remaining_text.lstrip()
        allowed_length = post_length - length_link_and_tags
        if not first_message:
            allowed_length = post_length - len(bot_handle) - 3
            message = bot_handle + " .." + message
        if len(message) > allowed_length:
            # strip message at last whitespace and account for 3 dots
            cut_position = message[: allowed_length - 3].rfind(" ")
            message = message[:cut_position]
            remaining_text = remaining_text[cut_position:]
            if cut_position + 3 > len(remaining_text):
                message = message.strip() + ".."
        else:
            remaining_text = ""
        if first_message:
            message = " ".join(
                filter(None, [message, link, conf_hashtags, phys_hashtags])
            )
            first_message = False
        message_list.append(message)
        logger.info("  '" + message + "'")
    return message_list


def tweet(
    twitter,
    type_hashtag,
    title,
    identifier,
    link,
    conf_hashtags,
    phys_hashtags,
    image_ids,
    post_gif,
    bot_handle,
):
    """tweet the new results with title and link and pictures taking care of length limitations."""
    # type_hashtag: title (identifier) link conf_hashtags
    logger.info("Creating tweet ...")
    # https://dev.twitter.com/rest/reference/get/help/configuration
    tweet_allowed_length = 280
    message_list = split_text(
        type_hashtag,
        title,
        identifier,
        link,
        conf_hashtags,
        phys_hashtags,
        tweet_allowed_length,
        bot_handle,
    )
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
                    if image_ids:
                        response = twitter.create_tweet(
                            text=message, media_ids=image_ids
                        )
                    else:
                        response = twitter.create_tweet(text=message)
                except tweepy.TweepyException as tweepy_exception:
                    logger.error(
                        f"TweepyException during first message (GIF) tweet: {tweepy_exception}"
                    )
                    logger.error(f"Response state: {response}")
                    sys.exit(1)
                first_message = False
                logger.debug(response)
            else:
                try:
                    response = twitter.create_tweet(
                        text=message, in_reply_to_tweet_id=previous_status_id
                    )
                except tweepy.TweepyException as tweepy_exception:
                    logger.error(
                        f"TweepyException during subsequent message (GIF) tweet: {tweepy_exception}"
                    )
                    logger.error(f"Response state: {response}")
                    return None
                logger.debug(response)
        else:
            try:
                if image_ids:
                    response = twitter.create_tweet(
                        text=message,
                        media_ids=image_ids[i * 4 : (i + 1) * 4],
                        in_reply_to_status_id=previous_status_id,
                    )
                else:
                    response = twitter.create_tweet(
                        text=message,
                        in_reply_to_status_id=previous_status_id,
                    )
            except tweepy.TweepyException as tweepy_exception:
                logger.error(f"TweepyException during image tweet: {tweepy_exception}")
                logger.error(f"Response state: {response}")
                return None
            logger.debug(response)
    return response


def toot(
    mastodon_client,
    type_hashtag,
    title,
    identifier,
    link,
    conf_hashtags,
    phys_hashtags,
    image_ids,
    post_gif,
    bot_handle,
):
    """toot the new results with title and link and pictures taking care of length limitations."""
    # type_hashtag: title (identifier) link conf_hashtags
    logger.info("Creating toot ...")
    toot_allowed_length = 500
    message_list = split_text(
        type_hashtag,
        title,
        identifier,
        link,
        conf_hashtags,
        phys_hashtags,
        toot_allowed_length,
        bot_handle,
    )
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
                    if image_ids:
                        response = mastodon_client.status_post(
                            status=message, media_ids=image_ids
                        )
                    else:
                        response = mastodon_client.status_post(status=message)
                except mastodon.MastodonError as mastodon_exception:
                    logger.error(
                        f"MastodonError during first message (GIF) toot: {mastodon_exception}"
                    )
                    logger.error(f"Response state: {response}")
                    return None
                first_message = False
                logger.debug(response)
            else:
                try:
                    response = mastodon_client.status_post(
                        status=message, in_reply_to_id=previous_status_id
                    )
                except mastodon.MastodonError as mastodon_exception:
                    logger.error(
                        f"MastodonError during subsequent message (GIF) toot: {mastodon_exception}"
                    )
                    logger.error(f"Response state: {response}")
                    return None
                logger.debug(response)
        else:
            try:
                if image_ids:
                    response = mastodon_client.status_post(
                        status=message,
                        media_ids=image_ids[i * 4 : (i + 1) * 4],
                        in_reply_to_id=previous_status_id,
                    )
                else:
                    response = mastodon_client.status_post(
                        status=message,
                        in_reply_to_id=previous_status_id,
                    )
            except mastodon.MastodonError as mastodon_exception:
                logger.error(f"MastodonError during image toot: {mastodon_exception}")
                logger.error(f"Response state: {response}")
                return None
            logger.debug(response)
    return response


def skeet(
    bluesky_client,
    type_hashtag,
    title,
    identifier,
    link,
    conf_hashtags,
    phys_hashtags,
    image_blobs,  # List of blob objects from bluesky_upload_images
    bot_handle,
    previous_skeet_ref=None,  # StrongRef of the previous skeet in a thread
    root_skeet_ref=None,  # StrongRef of the root skeet in a thread
):
    """Post (skeet) the new results to BlueSky."""
    if (
        not bluesky_client
        or BlueskyClient is None
        or atproto_models is None
        or BlueskyAtpApiError is None
    ):
        logger.error("BlueSky client or models not available. Skipping skeet.")
        return None

    # BlueSky allows 300 chars per post.
    # Facets (links, mentions) count towards this limit.
    # Link cards are not yet fully supported by atproto for creation in the same way as text facets.
    # We will include the link directly in the text.
    skeet_allowed_length = 300

    message_list = split_text(
        type_hashtag,
        title,
        identifier,
        link,
        conf_hashtags,
        phys_hashtags,
        skeet_allowed_length,
        bot_handle,
    )

    logger.info("Creating skeet ...")
    response_summary = {}  # To store the URI and CID of the last successful skeet

    for i, message_text in enumerate(message_list):
        logger.info(f"Skeet part {i + 1}: {message_text}")
        logger.debug(f"Length: {len(message_text)}")

        embed_to_post = None
        if i == 0 and image_blobs:  # Only add images to the first skeet of a thread
            # Ensure image_blobs is a list of atproto_models.AppBskyEmbedImages.Image
            valid_image_objects = []
            if isinstance(image_blobs, list):  # Check if it's a list first
                for blob_item in image_blobs:
                    if isinstance(blob_item, atproto_models.AppBskyEmbedImages.Image):  # pyright: ignore [reportOptionalMemberAccess]
                        valid_image_objects.append(blob_item)
                    elif hasattr(blob_item, "blob") and hasattr(
                        blob_item, "alt"
                    ):  # Handle if it's a simple structure
                        # This case might occur if bluesky_upload_images returns a simpler list
                        # For now, we assume it returns the correct Image objects.
                        # If not, this part would need adjustment or bluesky_upload_images needs to ensure it.
                        logger.warning(
                            "Received a blob item that is not an Image object, attempting to adapt if possible or skipping."
                        )
                        # Potentially try to construct an Image object if blob_item has 'blob' and 'alt'
                        # For now, we'll be strict and expect Image objects.
                    else:
                        logger.warning(
                            f"Skipping invalid item in image_blobs: {type(blob_item)}"
                        )

            if valid_image_objects:
                embed_to_post = atproto_models.AppBskyEmbedImages.Main(
                    images=valid_image_objects
                )  # pyright: ignore [reportOptionalMemberAccess]
            elif image_blobs:  # If image_blobs was not empty but valid_image_objects is
                logger.warning(
                    "image_blobs was not empty, but no valid Image objects were found for embedding."
                )

        reply_ref_for_this_skeet = None
        if previous_skeet_ref and root_skeet_ref:
            reply_ref_for_this_skeet = atproto_models.AppBskyFeedPost.ReplyRef(  # pyright: ignore [reportOptionalMemberAccess]
                parent=previous_skeet_ref, root=root_skeet_ref
            )

        try:
            # Construct the record for the post
            post_record = (
                atproto_models.AppBskyFeedPost.Record(  # Changed from .Main to .Record
                    text=message_text,
                    created_at=bluesky_client.get_current_time_iso(),  # pyright: ignore [reportOptionalMemberAccess]
                    embed=embed_to_post
                    if i == 0
                    else None,  # Only first post gets media
                    reply=reply_ref_for_this_skeet,
                    # langs=langs, # TODO: Add language detection
                )
            )

            # Prepare data for create_record
            record_data = atproto_models.ComAtprotoRepoCreateRecord.Data(  # pyright: ignore [reportOptionalMemberAccess]
                repo=bluesky_client.me.did,  # pyright: ignore [reportOptionalMemberAccess, reportUnknownMemberType]
                collection=atproto_models.ids.AppBskyFeedPost,  # pyright: ignore [reportOptionalMemberAccess]
                record=post_record.dict(exclude_none=True),  # Convert record to dict
            )

            response = bluesky_client.com.atproto.repo.create_record(data=record_data)  # pyright: ignore [reportOptionalMemberAccess, reportUnknownMemberType]

            logger.debug(f"Skeet part {i + 1} response: {response}")
            current_skeet_strong_ref = atproto_models.create_strong_ref(response)  # pyright: ignore [reportOptionalMemberAccess]

            response_summary = {"uri": response.uri, "cid": response.cid}  # pyright: ignore [reportOptionalMemberAccess, reportAttributeAccessIssue]

            if i == 0:  # If this is the first skeet
                root_skeet_ref = current_skeet_strong_ref  # It becomes the root for subsequent replies
            previous_skeet_ref = (
                current_skeet_strong_ref  # Current skeet becomes parent for the next
            )

        except BlueskyAtpApiError as e:  # pyright: ignore [reportPossiblyUnboundVariable]
            logger.error(f"BlueSky API error during skeet part {i + 1}: {e}")
            if i == 0 and embed_to_post:  # If first post with media failed
                logger.info(
                    "BlueSky: Skeet with media failed. Attempting skeet without media."
                )
                try:
                    post_record_no_media = atproto_models.AppBskyFeedPost.Record(  # Changed from .Main to .Record
                        text=message_text,
                        created_at=bluesky_client.get_current_time_iso(),  # pyright: ignore [reportOptionalMemberAccess]
                        reply=reply_ref_for_this_skeet,
                        # langs=langs,
                    )
                    record_data_no_media = (
                        atproto_models.ComAtprotoRepoCreateRecord.Data(  # pyright: ignore [reportOptionalMemberAccess]
                            repo=bluesky_client.me.did,  # pyright: ignore [reportOptionalMemberAccess, reportUnknownMemberType]
                            collection=atproto_models.ids.AppBskyFeedPost,  # pyright: ignore [reportOptionalMemberAccess]
                            record=post_record_no_media.dict(exclude_none=True),
                        )
                    )
                    response = bluesky_client.com.atproto.repo.create_record(
                        data=record_data_no_media
                    )  # pyright: ignore [reportOptionalMemberAccess, reportUnknownMemberType]

                    logger.debug(
                        f"Skeet part {i + 1} (no media fallback) response: {response}"
                    )
                    current_skeet_strong_ref = atproto_models.create_strong_ref(
                        response
                    )  # pyright: ignore [reportOptionalMemberAccess]
                    response_summary = {"uri": response.uri, "cid": response.cid}  # pyright: ignore [reportOptionalMemberAccess, reportAttributeAccessIssue]

                    if i == 0:
                        root_skeet_ref = current_skeet_strong_ref
                    previous_skeet_ref = current_skeet_strong_ref
                except Exception as e_fallback:
                    logger.error(
                        f"BlueSky: Skeet without media (fallback) also failed for part {i + 1}: {e_fallback}"
                    )
                    return None  # Failed even without media
            else:  # If non-first post failed, or first post without media failed
                return None  # Stop trying for this item
        except Exception as e:
            logger.error(f"Generic error during skeet part {i + 1}: {e}")
            # Similar fallback for generic errors on the first post with media
            if i == 0 and embed_to_post:
                logger.info(
                    "BlueSky: Skeet with media failed (generic error). Attempting skeet without media."
                )
                try:
                    post_record_no_media_generic = atproto_models.AppBskyFeedPost.Record(  # Changed from .Main to .Record
                        text=message_text,
                        created_at=bluesky_client.get_current_time_iso(),  # pyright: ignore [reportOptionalMemberAccess]
                        reply=reply_ref_for_this_skeet,
                        # langs=langs,
                    )
                    record_data_no_media_generic = (
                        atproto_models.ComAtprotoRepoCreateRecord.Data(  # pyright: ignore [reportOptionalMemberAccess]
                            repo=bluesky_client.me.did,  # pyright: ignore [reportOptionalMemberAccess, reportUnknownMemberType]
                            collection=atproto_models.ids.AppBskyFeedPost,  # pyright: ignore [reportOptionalMemberAccess]
                            record=post_record_no_media_generic.dict(exclude_none=True),
                        )
                    )
                    response = bluesky_client.com.atproto.repo.create_record(
                        data=record_data_no_media_generic
                    )  # pyright: ignore [reportOptionalMemberAccess, reportUnknownMemberType]

                    logger.debug(
                        f"Skeet part {i + 1} (no media fallback, generic error) response: {response}"
                    )
                    current_skeet_strong_ref = atproto_models.create_strong_ref(
                        response
                    )  # pyright: ignore [reportOptionalMemberAccess]
                    response_summary = {"uri": response.uri, "cid": response.cid}  # pyright: ignore [reportOptionalMemberAccess, reportAttributeAccessIssue]

                    if i == 0:
                        root_skeet_ref = current_skeet_strong_ref
                    previous_skeet_ref = current_skeet_strong_ref
                except Exception as e_fallback_generic:
                    logger.error(
                        f"BlueSky: Skeet without media (fallback after generic error) also failed for part {i + 1}: {e_fallback_generic}"
                    )
                    return None
            else:
                return None  # Stop trying for this item

        # If there are more messages, wait a bit before posting the next part of the thread
        if i < len(message_list) - 1:
            time.sleep(2)  # Short delay for threading

    return response_summary  # Return the URI and CID of the last (or only) skeet


def check_id_exists(identifier, feed_id, prefix=""):
    """Check with ID of the analysis already exists in text file to avoid tweeting again."""
    txt_file_name = f"{prefix}{feed_id}.txt"
    # create file if it doesn't exist yet
    if not os.path.isfile(txt_file_name):
        open(txt_file_name, "a").close()
    with open(txt_file_name) as txt_file:
        for line in txt_file:
            if identifier == line.strip("\n"):
                return True
    return False


def store_id(identifier, feed_id, prefix=""):
    """Store ID of the analysis in text file to avoid tweeting again."""
    txt_file_name = f"{prefix}{feed_id}.txt"
    with open(txt_file_name, "a") as txt_file:
        txt_file.write("%s\n" % identifier)


def main():
    """Main function."""
    dry_run = False  # run without tweeting
    analysis_id = ""
    keep_image_dir = False
    list_analyses = False
    post_gif = True
    use_arxiv_link = False

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--dry", help="perform dry run without tweeting", action="store_true"
    )
    parser.add_argument(
        "-v", "--verbose", help="enable verbose output", action="store_true"
    )
    parser.add_argument("-a", "--analysis", help="tweet specific analysis", type=str)
    parser.add_argument(
        "-m", "--max", help="maximum number of analyses to tweet", type=int, default=3
    )
    parser.add_argument(
        "-k", "--keep", help="keep image directory", action="store_true"
    )
    parser.add_argument(
        "-l", "--list", help="list analyses for feeds, then quit", action="store_true"
    )
    parser.add_argument("-g", "--nogif", help="do not create GIF", action="store_true")
    parser.add_argument(
        "-f",
        "--figmax",
        help="maximum number of figures to use for GIF",
        type=int,
        default=20,
    )
    parser.add_argument(
        "-e", "--experiment", help="experiment to tweet for", type=str, default="CMS"
    )
    parser.add_argument(
        "-c",
        "--config",
        help="name of feeds config file",
        type=str,
        default="feeds.ini",
    )
    parser.add_argument(
        "--auth", help="name of auth config file", type=str, default="auth.ini"
    )
    parser.add_argument("--arXiv", help="use arXiv link", action="store_true")
    args = parser.parse_args()
    max_tweets = args.max
    max_figures = args.figmax
    if args.dry:
        dry_run = True
    if args.verbose:
        global logger
        logger.setLevel(logging.DEBUG)
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
    use_arxiv_link = args.arXiv

    config = load_config(experiment, feed_file, auth_file)

    feed_entries = []
    for key in config["FEED_DICT"]:
        logger.info(f"Getting feed for {key}")
        this_feed = read_feed(config["FEED_DICT"][key])
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
        for post in sorted(
            feed_entries,
            key=lambda x: (x["feed_id"], maya.parse(x["published"]).datetime()),
        ):
            logger.info(
                " - {post_id} ({feed_id}), published {date}".format(
                    post_id=post["dc_source"],
                    feed_id=post["feed_id"],
                    date=post["published"],
                )
            )
        return
    twitter_client = twitter_auth(config["AUTH"])
    mastodon_client = mastodon_auth(config["AUTH"])
    bluesky_client = None
    if BlueskyClient is not None:  # Check if atproto was imported
        bluesky_client = bluesky_auth(config["AUTH"])
        if bluesky_client is None:
            logger.info(
                "BlueSky client initialization failed, BlueSky features will be skipped."
            )
    else:
        logger.info(
            "BlueSky library (atproto) not installed at top level, skipping BlueSky features."
        )

    # loop over posts sorted by date
    tweet_count = 0
    toot_count = 0
    skeet_count = 0  # New counter for BlueSky
    for post in sorted(
        feed_entries, key=lambda x: maya.parse(x["published"]).datetime()
    ):
        do_toot = True
        do_tweet = True
        do_skeet = True
        downloaded_image_list = []
        n_figures = 0
        downloaded_doc_list = []
        logger.debug(post)
        identifier = post["dc_source"]
        # fix wrong PAS name:
        parse_result = re.match(r"(CMS-PAS-).{3}-([A-Z]{3}-\d{2}-\d{3})-.*", identifier)
        if parse_result:
            new_identifier = parse_result.group(1) + parse_result.group(2)
            logger.info(f"Replacing ID {identifier} by {new_identifier}")
            identifier = new_identifier
        if analysis_id:
            if analysis_id not in identifier:
                continue
            else:
                logger.info("Found %s in feed %s" % (identifier, post["feed_id"]))
        else:
            if twitter_client:
                if check_id_exists(identifier, post["feed_id"], prefix="TWITTER_"):
                    logger.debug(
                        "%s has already been tweeted for feed %s"
                        % (identifier, post["feed_id"])
                    )
                    do_tweet = False
            else:
                do_tweet = False
            if mastodon_client:
                if check_id_exists(identifier, post["feed_id"], prefix="MASTODON_"):
                    logger.debug(
                        "%s has already been tooted for feed %s"
                        % (identifier, post["feed_id"])
                    )
                    do_toot = False
            else:
                do_toot = False

            if bluesky_client:  # Only check if client is available
                if check_id_exists(identifier, post["feed_id"], prefix="BLUESKY_"):
                    logger.debug(
                        "%s has already been skeeted for feed %s"
                        % (identifier, post["feed_id"])
                    )
                    do_skeet = False
            else:  # If client is None (not configured or auth failed)
                do_skeet = False

        if not do_toot and not do_tweet and not do_skeet:  # Updated condition
            continue
        logger.info(
            "{id} - published: {date}".format(
                id=identifier, date=maya.parse(post["published"]).datetime()
            )
        )

        arxiv_id = ""
        # try to find arXiv ID
        if identifier.startswith("arXiv"):
            arxiv_id = identifier.rsplit(":", 1)[1]
            logger.info("Found arXiv ID arXiv:%s" % arxiv_id)
            arxiv_link = "https://arxiv.org/abs/%s" % arxiv_id
            logger.debug(arxiv_link)
            request = requests.get(arxiv_link)
            if request.status_code >= 400:
                logger.warning(f"arXiv URL {arxiv_link} seems invalid")
                arxiv_link = None

        # looking for media
        media_content = []
        if "media_content" in post:
            media_content += post["media_content"]
        outdir = identifier.replace(":", "_")
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        logger.debug("Attempting to download media.")
        # media also includes on the physics
        phys_hashtags = ""
        for media in media_content:
            media_url = media["url"]
            media_found = False
            media_isimage = False
            if media_url.find("cadi?ancode=") >= 0:
                parse_result = re.match(r".*ancode=(\w{3})-\d{2}-\d{3}", media_url)
                if parse_result:
                    if parse_result[1] in CADI_TO_HASHTAG:
                        phys_hashtags = CADI_TO_HASHTAG[parse_result[1]]
                        logger.info(f"Found physics tag: {phys_hashtags}")
            # consider only attached figures and main doc
            if experiment == "CMS":
                # CMS follows a certain standard
                # but figures can be both PDF and PNG
                if re.search(r"/files\/.*[Ff]igures?_", media_url):
                    media_found = True
                    media_isimage = True
            elif experiment == "ATLAS":
                # ATLAS seems to only use PNG format for plots
                if media_url.lower().endswith(".png"):
                    media_found = True
                    media_isimage = True
                elif re.search(
                    r"^" + re.escape(post.link) + "/files\/(?![Ff]ig).*\.pdf$",
                    media_url,
                ):
                    media_found = True
            # check if media can be downloaded
            if media_found:
                media_url = media_url.split("?", 1)[0]
                logger.debug("media: " + media_url)
                request = requests.get(media_url, timeout=10)
                if not request.status_code < 400:
                    logger.error("media: " + media_url + " does not exist!")
                    media_found = False
            # download and categorise media
            if media_found:
                # download images
                out_path = "{}/{}".format(outdir, media_url.rsplit("/", 1)[1])
                request = requests.get(media_url, stream=True)
                if request.status_code == 200:
                    with open(out_path, "wb") as file_handler:
                        request.raw.decode_content = True
                        shutil.copyfileobj(request.raw, file_handler)
                    if out_path.find("%") >= 0:
                        continue
                    if media_isimage:
                        downloaded_image_list.append(out_path)
                        logger.debug("image: " + out_path + " downloaded!")
                        n_figures += 1
                    else:
                        downloaded_doc_list.append(out_path)
                        logger.debug("doc: " + out_path + " downloaded!")
            if n_figures >= max_figures:
                break

        # ATLAS notes workaround
        if experiment == "ATLAS" and len(downloaded_image_list) == 0:
            confnotepageurl = (
                "https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/CONFNOTES/"
                + identifier
                + "/"
            )
            linkedimages = read_html(confnotepageurl).xpath("//a[img]/@href")
            for image in linkedimages:
                # ATLAS only uses PNG format for plots
                if not image.lower().endswith(".png"):
                    continue
                # skip tables and aux for this purpose
                if image.lower().startswith("tab") or "aux" in image.lower():
                    continue
                # now this part is (for now) just a copy-n-paste from above (sorry about that)
                media_found = True
                media_url = confnotepageurl + image
                logger.debug("media: " + media_url)
                request = requests.get(media_url, timeout=10)
                if not request.status_code < 400:
                    logger.error("media: " + media_url + " does not exist!")
                    media_found = False

                if media_found:
                    # download images
                    out_path = "{}/{}".format(outdir, media_url.rsplit("/", 1)[1])
                    request = requests.get(media_url, stream=True)
                    if request.status_code == 200:
                        with open(out_path, "wb") as file_handler:
                            request.raw.decode_content = True
                            shutil.copyfileobj(request.raw, file_handler)
                        if out_path.find("%") >= 0:
                            continue
                        downloaded_image_list.append(out_path)

        # if there's a zip file and only one PDF, the figures are probably in the zip file
        if any(".zip" in s for s in downloaded_image_list):
            logger.info("using zip file instead of images")
            zipfile_name = [s for s in downloaded_image_list if ".zip" in s][0]
            downloaded_image_list = []
            outzip = f"{outdir}/zipdir"
            os.makedirs(outzip)
            with zipfile.ZipFile(zipfile_name) as myzip:
                myzip.extractall(outzip)
            image_list = list(Path(outzip).rglob("*.pdf"))
            # need to convert PosixPath to str
            str_image_list = [str(img_path) for img_path in image_list]
            # ignore some files
            for img_path in sorted(str_image_list):
                if not (
                    (img_path.find("lhcb-logo.pdf") >= 0)
                    or (img_path.find("__MACOSX") >= 0)
                    or (img_path.rsplit("/", 1)[1].startswith("."))
                ):
                    downloaded_image_list.append(img_path)

        twitter_image_ids = []
        mastodon_image_ids = []
        bluesky_image_blobs = []

        if downloaded_image_list:
            # Twitter processing and upload
            if twitter_client:
                try:
                    logger.info(
                        f"Twitter: Initial media processing & upload (post_gif={post_gif})."
                    )
                    # Process images for Twitter based on the global post_gif flag.
                    # Twitter's own fallback logic is handled later in the tweet() function if this upload succeeds but tweeting fails.
                    image_list_for_twitter = process_images(
                        outdir, downloaded_image_list, post_gif
                    )
                    twitter_image_ids = twitter_upload_images(
                        twitter_client["v1"], image_list_for_twitter, post_gif
                    )
                except (
                    tweepy.TweepyException
                ) as e:  # Assuming twitter_upload_images might be changed to raise this
                    logger.error(
                        f"Twitter: Initial media upload failed: {e}. Media IDs will be empty."
                    )
                    twitter_image_ids = []
                except Exception as e_twitter_proc:  # Catch other errors like from process_images for twitter
                    logger.error(
                        f"Twitter: Error during initial media processing for Twitter: {e_twitter_proc}"
                    )
                    twitter_image_ids = []

            # Mastodon processing and upload with fallback
            if mastodon_client:
                current_post_gif_for_mastodon = post_gif  # Start with global setting
                processed_image_list_for_mastodon = []  # To hold images processed for Mastodon

                try:
                    # Attempt 1 (potentially GIF)
                    logger.info(
                        f"Mastodon: Initial media processing (post_gif={current_post_gif_for_mastodon})."
                    )
                    processed_image_list_for_mastodon = process_images(
                        outdir,
                        downloaded_image_list,
                        current_post_gif_for_mastodon,
                    )
                    logger.info(
                        f"Mastodon: Attempting initial media upload with {len(processed_image_list_for_mastodon)} item(s)."
                    )
                    mastodon_image_ids = mastodon_upload_images(
                        mastodon_client,
                        processed_image_list_for_mastodon,
                        current_post_gif_for_mastodon,
                    )
                except mastodon.MastodonError as e:  # Catch any MastodonError first
                    logger.warning(
                        f"Mastodon: Media upload attempt 1 failed with MastodonError: {e}"
                    )
                    if (
                        current_post_gif_for_mastodon
                        and isinstance(e, mastodon.MastodonAPIError)
                        and hasattr(e, "http_status")
                        and e.http_status == 422
                    ):
                        logger.info(
                            f"Mastodon: Specific MastodonAPIError (422) for GIF detected. Retrying without GIF."
                        )
                        current_post_gif_for_mastodon = False  # Fallback: No GIF
                        try:
                            logger.info(
                                f"Mastodon: Fallback media processing (post_gif={current_post_gif_for_mastodon})."
                            )
                            processed_image_list_for_mastodon = process_images(
                                outdir,
                                downloaded_image_list,
                                current_post_gif_for_mastodon,
                            )  # Re-process
                            logger.info(
                                f"Mastodon: Attempting fallback media upload with {len(processed_image_list_for_mastodon)} item(s)."
                            )
                            mastodon_image_ids = mastodon_upload_images(
                                mastodon_client,
                                processed_image_list_for_mastodon,
                                current_post_gif_for_mastodon,
                            )
                        except (
                            mastodon.MastodonError
                        ) as e2:  # Catch errors during fallback upload
                            logger.error(
                                f"Mastodon: Media upload fallback attempt failed: {e2}"
                            )
                            mastodon_image_ids = []
                        except (
                            Exception
                        ) as e_fallback_proc:  # Catch errors during fallback processing
                            logger.error(
                                f"Mastodon: Error during fallback media processing: {e_fallback_proc}"
                            )
                            mastodon_image_ids = []
                    else:
                        # This was a MastodonError but not the specific 422 GIF error, or GIF was not attempted.
                        logger.error(
                            f"Mastodon: Media upload failed (MastodonError was not a 422 GIF error or GIF not attempted): {e}"
                        )
                        mastodon_image_ids = []
                except Exception as e_generic:  # Catch other errors like from process_images in the first attempt
                    logger.error(
                        f"Mastodon: Unexpected error during initial media preparation/upload: {e_generic}"
                    )
                    mastodon_image_ids = []

                logger.debug(
                    f"Mastodon image IDs after initial upload section: {mastodon_image_ids}"
                )

            # BlueSky processing and upload
            bluesky_image_blobs = []  # Initialize to empty list
            if bluesky_client and do_skeet:  # Check client and if we intend to skeet
                current_post_gif_for_bluesky = (
                    post_gif  # Start with global/user preference for GIF
                )

                # Attempt 1: Process and upload as GIF (if post_gif is True) or static images
                try:
                    logger.info(
                        f"BlueSky: Initial media processing (post_gif={current_post_gif_for_bluesky})."
                    )
                    # Use a different variable name to avoid confusion if process_images is called again for fallback
                    image_list_for_bluesky_attempt1 = process_images(
                        outdir,
                        downloaded_image_list,
                        post_gif=current_post_gif_for_bluesky,
                    )
                    if image_list_for_bluesky_attempt1:
                        bluesky_image_blobs = bluesky_upload_images(
                            bluesky_client, image_list_for_bluesky_attempt1, identifier
                        )
                    else:
                        logger.info("BlueSky: No images processed in first attempt.")
                        # bluesky_image_blobs remains empty
                except Exception as e_bsky_proc1:
                    logger.error(
                        f"BlueSky: Error during initial media processing/upload attempt: {e_bsky_proc1}"
                    )
                    bluesky_image_blobs = []  # Ensure it's empty on error

                # Attempt 2 (Fallback): If GIF was attempted (current_post_gif_for_bluesky was true)
                # and it resulted in no blobs, try static images.
                if not bluesky_image_blobs and current_post_gif_for_bluesky:
                    logger.info(
                        "BlueSky: GIF upload attempt failed or resulted in no blobs. Falling back to static images."
                    )
                    # Force static images for fallback by setting post_gif for this specific call to False
                    try:
                        logger.info(
                            "BlueSky: Fallback media processing (post_gif=False)."
                        )
                        image_list_for_bluesky_fallback = process_images(
                            outdir,
                            downloaded_image_list,
                            post_gif=False,  # Explicitly False for fallback
                        )
                        if image_list_for_bluesky_fallback:
                            bluesky_image_blobs = bluesky_upload_images(
                                bluesky_client,
                                image_list_for_bluesky_fallback,
                                identifier,
                            )
                        else:
                            logger.info(
                                "BlueSky: No images processed in fallback attempt."
                            )
                            # bluesky_image_blobs remains empty
                    except Exception as e_bsky_proc_fallback:
                        logger.error(
                            f"BlueSky: Error during fallback media processing/upload: {e_bsky_proc_fallback}"
                        )
                        bluesky_image_blobs = []  # Ensure it's empty on error

                if not bluesky_image_blobs:
                    logger.info(
                        "BlueSky: All media processing/upload attempts failed or yielded no images."
                    )

                logger.debug(
                    f"BlueSky image blobs after all attempts: {len(bluesky_image_blobs)} blobs."
                )

        title = post.title
        link = post.link
        if use_arxiv_link and arxiv_id:
            link = arxiv_link

        prelim_result = False
        for item in PRELIM:
            if identifier.find(item) >= 0:
                prelim_result = True
                logger.info("This is a preliminary result.")

        conf_hashtags = ""
        # use only for PAS/CONF notes:
        if prelim_result:
            conf_hashtags = " ".join(
                filter(None, (conf.is_now(post["published"]) for conf in CONFERENCES))
            )
            logger.info(f"Conference hashtags: {conf_hashtags}")

        type_hashtag = "New result"
        if prelim_result:
            if experiment == "CMS":
                type_hashtag = "#CMSPAS"
            else:
                type_hashtag = f"#{experiment}conf"
        else:
            type_hashtag = f"#{experiment}paper"
            # For initial submission to arXiv there won't be any pictures,
            # but the submission happens days before the analysis appears on arXiv
            # while the CDS entry with the arXiv identifier comes after the
            # availability on arXiv, so let's give people a heads-up of what's coming.
            if (experiment == "CMS" or experiment == "LHCb") and identifier.startswith(
                "CERN-EP"
            ):
                type_hashtag += " soon on arXiv"

        title_formatted = format_title(title)
        if sys.version_info[0] < 3:
            title_formatted = title_formatted.encode("utf8")

        # title_temp = type_hashtag + ": " + title_formatted + " (" + identifier + ") " + link + " " + conf_hashtags
        # logger.info(title_temp)

        # skip entries without media for ATLAS
        if downloaded_image_list or experiment != "ATLAS":
            if twitter_client:
                tweet_count += 1
                if not dry_run:
                    tweet_response = tweet(
                        twitter_client["v2"],
                        type_hashtag,
                        title_formatted,
                        identifier,
                        link,
                        conf_hashtags,
                        phys_hashtags,
                        twitter_image_ids,
                        post_gif,
                        config["AUTH"]["BOT_HANDLE"],
                    )
                    if not tweet_response:
                        # try to recover since something went wrong
                        # first, try to use individual images instead of GIF
                        if post_gif:
                            if downloaded_image_list:
                                logger.info("Trying to tweet without GIF")
                                image_list = process_images(
                                    outdir, downloaded_image_list, post_gif=False
                                )
                                twitter_image_ids = twitter_upload_images(
                                    twitter_client["v1"], image_list, post_gif=False
                                )
                                tweet_response = tweet(
                                    twitter_client["v2"],
                                    type_hashtag,
                                    title_formatted,
                                    identifier,
                                    link,
                                    conf_hashtags,
                                    phys_hashtags,
                                    twitter_image_ids,
                                    post_gif=False,
                                    bot_handle=config["AUTH"]["BOT_HANDLE"],
                                )
                    if not tweet_response:
                        # second, try to tweet without image
                        logger.info("Trying to tweet without images")
                        tweet_response = tweet(
                            twitter_client["v2"],
                            type_hashtag,
                            title_formatted,
                            identifier,
                            link,
                            conf_hashtags,
                            phys_hashtags,
                            image_ids=[],
                            post_gif=False,
                            bot_handle=config["AUTH"]["BOT_HANDLE"],
                        )
                    if tweet_response:
                        store_id(identifier, post["feed_id"], prefix="TWITTER_")
                else:
                    logger.info("Tweet information:")
                    logger.info(title_formatted)
                    logger.info("identifier: " + identifier)
                    logger.info("link: " + link)
                    logger.info("type_hashtag: " + type_hashtag)
                    logger.info("conf_hashtags: " + conf_hashtags)
                    logger.info("phys_hashtags: " + phys_hashtags)
            if mastodon_client:
                toot_count += 1
                if not dry_run:
                    logger.info(
                        "Waiting 10 seconds before first toot attempt for this item."
                    )
                    time.sleep(10)

                    mastodon_image_ids = []
                    actual_post_gif_for_mastodon = (
                        post_gif  # Variable to track if GIF is used for this toot
                    )

                    if downloaded_image_list:
                        try:
                            # Attempt 1: Process and upload (possibly as GIF)
                            logger.info(
                                f"Mastodon: Initial media processing (post_gif={actual_post_gif_for_mastodon})."
                            )
                            image_list_for_mastodon = process_images(
                                outdir,
                                downloaded_image_list,
                                actual_post_gif_for_mastodon,
                            )
                            mastodon_image_ids = mastodon_upload_images(
                                mastodon_client,
                                image_list_for_mastodon,
                                actual_post_gif_for_mastodon,
                            )
                        except (
                            mastodon.MastodonError
                        ) as e:  # Changed from MastodonAPIError to MastodonError
                            logger.warning(
                                f"Mastodon: Media upload attempt 1 failed: {e}"
                            )
                            # Check if it's the specific API error we want to handle for GIF fallback
                            if (
                                actual_post_gif_for_mastodon
                                and isinstance(e, mastodon.MastodonAPIError)
                                and hasattr(e, "http_status")
                                and e.http_status == 422
                            ):
                                logger.info(
                                    "Mastodon: GIF upload failed with 422 (MastodonAPIError). Retrying media upload without GIF."
                                )
                                actual_post_gif_for_mastodon = False  # Fallback: No GIF
                                try:
                                    # Attempt 2: Process and upload as individual images
                                    logger.info(
                                        f"Mastodon: Fallback media processing (post_gif={actual_post_gif_for_mastodon})."
                                    )
                                    image_list_for_mastodon_fallback = process_images(
                                        outdir, downloaded_image_list, post_gif=False
                                    )
                                    mastodon_image_ids = mastodon_upload_images(
                                        mastodon_client,
                                        image_list_for_mastodon_fallback,
                                        post_gif=False,
                                    )
                                except mastodon.MastodonError as e2:
                                    logger.error(
                                        f"Mastodon: Media upload fallback attempt failed: {e2}"
                                    )
                                    mastodon_image_ids = []  # Failed to upload any media in fallback
                            else:
                                # This is a MastodonError that is not the specific 422 GIF error,
                                # or it was a MastodonAPIError not fitting the criteria.
                                logger.error(
                                    f"Mastodon: Unhandled MastodonError or non-422 API error during media upload: {e}"
                                )
                                mastodon_image_ids = []  # Failed to upload any media
                        except Exception as e_generic:  # Catch other potential errors (e.g., from process_images)
                            logger.error(
                                f"Mastodon: Unexpected error during media preparation: {e_generic}"
                            )
                            mastodon_image_ids = []  # Failed to prepare/upload any media

                    # Proceed with tooting attempts
                    toot_response = None
                    max_retry = 10
                    for attempt_num in range(max_retry):
                        toot_response = toot(
                            mastodon_client,
                            type_hashtag,
                            title_formatted,
                            identifier,
                            link,
                            conf_hashtags,
                            phys_hashtags,
                            mastodon_image_ids,  # Use the (possibly empty or fallback) list of IDs
                            actual_post_gif_for_mastodon,  # Use the final decision on GIF status
                            config["AUTH"]["MASTODON_BOT_HANDLE"],
                        )
                        if toot_response:
                            store_id(identifier, post["feed_id"], prefix="MASTODON_")
                            break
                        # If toot failed, and it's not the last attempt, log and wait
                        if not toot_response and attempt_num < max_retry - 1:
                            logger.info(
                                f"Mastodon: Toot attempt {attempt_num + 1}/{max_retry} failed. Waiting 10 seconds before next attempt."
                            )
                            time.sleep(10)

                    # Final fallback: If all toot attempts failed and images were originally present (implying media was intended)
                    if not toot_response and downloaded_image_list:
                        logger.info(
                            "Mastodon: All toot attempts (possibly with media) failed. Attempting a final toot explicitly without media."
                        )
                        final_fallback_toot_response = toot(
                            mastodon_client,
                            type_hashtag,
                            title_formatted,
                            identifier,
                            link,
                            conf_hashtags,
                            phys_hashtags,
                            image_ids=[],  # Explicitly no media
                            post_gif=False,  # GIF status irrelevant here
                            bot_handle=config["AUTH"]["MASTODON_BOT_HANDLE"],
                        )
                        if final_fallback_toot_response:
                            store_id(identifier, post["feed_id"], prefix="MASTODON_")

                else:  # This is the dry_run part
                    logger.info("Mastodon: Dry run, toot information:")
                    logger.info(title_formatted)
                    logger.info("identifier: " + identifier)
                    logger.info("link: " + link)
                    logger.info("type_hashtag: " + type_hashtag)
                    logger.info("conf_hashtags: " + conf_hashtags)
                    logger.info("phys_hashtags: " + phys_hashtags)

            if bluesky_client and do_skeet:
                skeet_count += 1
                if not dry_run:
                    logger.info(
                        "Waiting 5 seconds before first skeet attempt for this item."
                    )
                    time.sleep(5)

                    skeet_response = skeet(
                        bluesky_client,
                        type_hashtag,
                        title_formatted,
                        identifier,
                        link,
                        conf_hashtags,
                        phys_hashtags,
                        bluesky_image_blobs,
                        config["AUTH"].get("BLUESKY_HANDLE", ""),
                    )

                    if not skeet_response and bluesky_image_blobs:
                        logger.info(
                            "BlueSky: Skeet with media failed. Attempting skeet without media."
                        )
                        time.sleep(5)
                        skeet_response = skeet(
                            bluesky_client,
                            type_hashtag,
                            title_formatted,
                            identifier,
                            link,
                            conf_hashtags,
                            phys_hashtags,
                            [],
                            config["AUTH"].get("BLUESKY_HANDLE", ""),
                        )

                    if skeet_response:
                        store_id(identifier, post["feed_id"], prefix="BLUESKY_")
                        logger.info(
                            f"BlueSky: Successfully skeeted. URI: {skeet_response.get('uri')}"
                        )
                    else:
                        logger.error(
                            "BlueSky: All skeet attempts failed for this item."
                        )

                else:
                    logger.info("BlueSky: Dry run, skeet information:")
                    # Simpler dry run log for BlueSky, focusing on the combined text from split_text
                    temp_message_list_for_dry_run = split_text(
                        type_hashtag,
                        title_formatted,
                        identifier,
                        link,
                        conf_hashtags,
                        phys_hashtags,
                        300,  # skeet_allowed_length
                        config["AUTH"].get("BLUESKY_HANDLE", ""),
                    )
                    for i, dry_message in enumerate(temp_message_list_for_dry_run):
                        logger.info(f"Skeet part {i + 1} (dry run): {dry_message}")

                    logger.info(
                        f"Number of images prepared for BlueSky (dry run): {len(bluesky_image_blobs)}"
                    )
                    logger.info("Identifier (dry run): " + identifier)

        if not keep_image_dir:
            # clean up images
            shutil.rmtree(outdir)
        if (
            tweet_count >= max_tweets
            or toot_count >= max_tweets
            or skeet_count >= max_tweets
        ):  # Updated condition
            logger.info(f"Reached max posts limit ({max_tweets}). Exiting.")
            return


if __name__ == "__main__":
    main()
