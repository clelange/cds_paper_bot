"""Twitter bot to post latest CMS results."""

from __future__ import print_function

import argparse
import atexit
import configparser
import concurrent.futures
import hashlib
import json
import logging
import os
import re
import shutil
import sys
import time
import zipfile
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlparse

import daiquiri
import feedparser
import lxml.html as lh
import mastodon
import maya
import requests
import tweepy

# Assuming atproto is installed
from atproto import Client as BlueskyClient
from atproto import models as atproto_models
from atproto.exceptions import AtProtocolError as BlueskyAtpApiError
from pylatexenc.latex2text import LatexNodes2Text
from pylatexenc.latexwalker import LatexWalkerError

from paperbot.media import natural_sort_key, order_media, prepare_media_sequence
from paperbot.models import Publication, RunSummary, lifecycle_stage_for
from paperbot.rendering import BlueskyRenderer, MastodonRenderer, render_messages
from paperbot.state import (
    DeliveryLedger,
    find_existing_bluesky_post,
    find_existing_mastodon_post,
)

daiquiri.setup(level=logging.INFO)
logger = daiquiri.getLogger()  # pylint: disable=invalid-name

REQUEST_TIMEOUT = float(os.getenv("CDS_REQUEST_TIMEOUT", "10"))
REQUEST_RETRIES = int(os.getenv("CDS_REQUEST_RETRIES", "3"))
REQUEST_RETRY_DELAY = float(os.getenv("CDS_REQUEST_RETRY_DELAY", "2"))


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


def _request_context(phase, experiment=None, feed_id=None, identifier=None):
    """Format request context for logs."""
    context = [f"phase={phase}"]
    if experiment:
        context.append(f"experiment={experiment}")
    if feed_id:
        context.append(f"feed_id={feed_id}")
    if identifier:
        context.append(f"identifier={identifier}")
    return ", ".join(context)


def request_with_retries(
    url,
    phase,
    experiment=None,
    feed_id=None,
    identifier=None,
    stream=False,
    timeout=REQUEST_TIMEOUT,
    retries=REQUEST_RETRIES,
    retry_delay=REQUEST_RETRY_DELAY,
):
    """Request a URL with short retries for transient network failures."""
    context = _request_context(phase, experiment, feed_id, identifier)
    for attempt in range(1, retries + 1):
        try:
            return requests.get(url, timeout=timeout, stream=stream)
        except (requests.Timeout, requests.ConnectionError) as request_exception:
            logger.warning(
                "Transient request failure (%s, attempt=%d/%d, url=%s): %s: %s",
                context,
                attempt,
                retries,
                url,
                request_exception.__class__.__name__,
                request_exception,
            )
            if attempt < retries:
                time.sleep(retry_delay)
        except requests.RequestException as request_exception:
            logger.warning(
                "Request failed (%s, url=%s): %s: %s",
                context,
                url,
                request_exception.__class__.__name__,
                request_exception,
            )
            return None

    logger.warning("Giving up request (%s, attempts=%d, url=%s)", context, retries, url)
    return None


def media_url_exists(
    media_url,
    experiment=None,
    feed_id=None,
    identifier=None,
    timeout=REQUEST_TIMEOUT,
    retries=REQUEST_RETRIES,
    retry_delay=REQUEST_RETRY_DELAY,
):
    """Check whether a media URL can be reached without failing the bot run."""
    request = request_with_retries(
        media_url,
        phase="media check",
        experiment=experiment,
        feed_id=feed_id,
        identifier=identifier,
        timeout=timeout,
        retries=retries,
        retry_delay=retry_delay,
    )
    if request is None:
        logger.warning("Skipping media after failed check: %s", media_url)
        return False
    try:
        if request.status_code >= 400:
            logger.error("media: " + media_url + " does not exist!")
            return False
        return True
    finally:
        close_response = getattr(request, "close", None)
        if close_response:
            close_response()


def download_media_url(
    media_url,
    out_path,
    experiment=None,
    feed_id=None,
    identifier=None,
    timeout=REQUEST_TIMEOUT,
    retries=REQUEST_RETRIES,
    retry_delay=REQUEST_RETRY_DELAY,
):
    """Download media and remove partial files on streaming failures."""
    request = request_with_retries(
        media_url,
        phase="media download",
        experiment=experiment,
        feed_id=feed_id,
        identifier=identifier,
        stream=True,
        timeout=timeout,
        retries=retries,
        retry_delay=retry_delay,
    )
    if request is None:
        logger.warning("Skipping media after failed download: %s", media_url)
        return False
    if request.status_code != 200:
        logger.warning(
            "Skipping media download with status %s: %s", request.status_code, media_url
        )
        return False

    try:
        with open(out_path, "wb") as file_handler:
            request.raw.decode_content = True
            shutil.copyfileobj(request.raw, file_handler)
    except Exception as download_exception:  # pylint: disable=broad-except
        logger.warning(
            "Failed while streaming media download (%s, url=%s): %s: %s",
            _request_context(
                "media download", experiment, feed_id=feed_id, identifier=identifier
            ),
            media_url,
            download_exception.__class__.__name__,
            download_exception,
        )
        if os.path.exists(out_path):
            os.remove(out_path)
        return False
    finally:
        close_response = getattr(request, "close", None)
        if close_response:
            close_response()

    return True


def _media_filename(media_url, index):
    """Return a filesystem-safe attachment name while retaining its extension."""
    filename = Path(unquote(urlparse(media_url).path)).name
    filename = re.sub(r"[^A-Za-z0-9._-]+", "_", filename).strip("._")
    return filename or f"media-{index:03d}"


def download_media_candidates(
    candidates,
    output_directory,
    *,
    experiment,
    feed_id,
    identifier,
    workers=4,
    time_budget=120,
):
    """Download each URL once with bounded concurrency and stable result order."""
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    unique_candidates = []
    seen_urls = set()
    seen_filenames = set()
    for media_url, media_kind in candidates:
        clean_url = media_url.split("?", 1)[0]
        filename = _media_filename(clean_url, len(unique_candidates))
        if clean_url in seen_urls or filename.casefold() in seen_filenames:
            continue
        seen_urls.add(clean_url)
        seen_filenames.add(filename.casefold())
        unique_candidates.append((clean_url, media_kind))

    def download_one(index, media_url, media_kind):
        output_path = output_directory / _media_filename(media_url, index)
        if download_media_url(
            media_url,
            str(output_path),
            experiment=experiment,
            feed_id=feed_id,
            identifier=identifier,
        ):
            return index, media_kind, output_path
        return index, media_kind, None

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers))
    futures = [
        executor.submit(download_one, index, media_url, media_kind)
        for index, (media_url, media_kind) in enumerate(unique_candidates)
    ]
    done, pending = concurrent.futures.wait(futures, timeout=time_budget)
    for future in pending:
        future.cancel()
    executor.shutdown(wait=not pending, cancel_futures=True)
    if pending:
        logger.warning(
            "Media download budget exhausted after %s seconds; cancelled %d item(s)",
            time_budget,
            len(pending),
        )
    results = []
    for future in done:
        try:
            result = future.result()
        except Exception as exception:  # pylint: disable=broad-except
            logger.warning("Media download worker failed: %s", exception)
            continue
        if result[2] is not None:
            results.append(result)
    return [(kind, path) for _, kind, path in sorted(results)]


def safe_extract_lhcb_figures(zip_path, output_directory, maximum_figures):
    """Extract only bounded PDF figures from an LHCb attachment."""
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    extracted = []
    with zipfile.ZipFile(zip_path) as archive:
        candidates = sorted(
            (
                item
                for item in archive.infolist()
                if not item.is_dir()
                and item.filename.casefold().endswith(".pdf")
                and "lhcb-logo.pdf" not in item.filename.casefold()
                and "__macosx" not in item.filename.casefold()
                and not Path(item.filename).name.startswith(".")
            ),
            key=lambda item: natural_sort_key(item.filename),
        )
        for index, item in enumerate(candidates[:maximum_figures], start=1):
            if item.file_size > 50 * 1024 * 1024:
                logger.warning("Skipping oversized ZIP member %s", item.filename)
                continue
            destination = output_directory / f"{index:03d}-{Path(item.filename).name}"
            with archive.open(item) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)
            extracted.append(destination)
    return extracted


def response_value(response, key, default=""):
    """Read an API response field from either a mapping or object."""
    if isinstance(response, dict):
        return response.get(key, default)
    return getattr(response, key, default)


def read_feed(rss_url, feed_id=None, experiment=None):
    """read the RSS feed and return dictionary"""
    response = request_with_retries(
        rss_url,
        phase="RSS",
        experiment=experiment,
        feed_id=feed_id,
    )
    if response is None:
        return
    try:
        if response.status_code >= 400:
            logger.error(
                "RSS request returned HTTP %s: %s", response.status_code, rss_url
            )
            return
        content = BytesIO(response.content)
    finally:
        close_response = getattr(response, "close", None)
        if close_response:
            close_response()
    # Parse content
    feed = feedparser.parse(content)
    return feed


def read_html(html_url, experiment=None, feed_id=None, identifier=None):
    """read the HTML page and return dictionary"""
    response = request_with_retries(
        html_url,
        phase="HTML",
        experiment=experiment,
        feed_id=feed_id,
        identifier=identifier,
    )
    if response is None:
        return
    try:
        if response.status_code >= 400:
            logger.error(
                "HTML request returned HTTP %s: %s", response.status_code, html_url
            )
            return
        content = BytesIO(response.content)
    finally:
        close_response = getattr(response, "close", None)
        if close_response:
            close_response()
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
                    raise tweepy_exception
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
                raise tweepy_exception
            logger.info(response)
            image_ids.append(response.media_id)
    logger.info(image_ids)
    return image_ids


def mastodon_upload_images(mastodon_client, image_list, post_gif, alt_text=""):
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
                        description=alt_text
                        or f"Animated GIF image for {image_path.split('/')[0]}",
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
                    description=alt_text or f"Image for {image_path.split('/')[0]}",
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


def bluesky_upload_media(
    bluesky_client, media_list, identifier_for_alt_text, alt_text=""
):
    """Upload media (images or video) to BlueSky and return blob references."""
    if not bluesky_client:
        return []

    logger.info("Uploading media to BlueSky.")
    image_blobs = []

    # If we have a video file (converted GIF), try to upload it first
    mp4_files = [f for f in media_list if f.endswith(".mp4")]
    if mp4_files:
        video_path = mp4_files[0]
        logger.info(f"Attempting to upload video file: {video_path}")

        # Get video file size and other properties
        file_size = os.path.getsize(video_path)
        logger.info(f"Video file size: {file_size} bytes")
        try:
            with open(mp4_files[0], "rb") as f:
                video_data = f.read()

            blob_response = bluesky_client.com.atproto.repo.upload_blob(video_data)
            logger.info(f"Blob upload response: {blob_response}")
            video_alt_text = (
                alt_text or f"Video animation for {identifier_for_alt_text}"
            )

            # Create video embed
            video_blob = atproto_models.AppBskyEmbedVideo.Main(
                video=blob_response.blob, alt=video_alt_text
            )
            logger.info(f"Video blob: {video_blob}")
            return [video_blob]
        except Exception as e:
            logger.error(f"Failed to upload video, falling back to images: {e}")
            # Continue to image upload fallback

    # Fallback: Upload up to 4 static images
    for image_path in sorted(media_list)[:4]:
        if image_path.endswith(".mp4"):
            continue  # Skip mp4 files in image processing
        try:
            with open(image_path, "rb") as f:
                img_data = f.read()

            image_alt_text = alt_text or (
                f"Image for {identifier_for_alt_text}: {os.path.basename(image_path)}"
            )
            # Truncate alt text if too long
            max_alt_text_len = 500
            if len(image_alt_text) > max_alt_text_len:
                image_alt_text = image_alt_text[: max_alt_text_len - 3] + "..."

            response = bluesky_client.com.atproto.repo.upload_blob(img_data)
            image_blobs.append(
                atproto_models.AppBskyEmbedImages.Image(
                    image=response.blob, alt=image_alt_text
                )
            )
            logger.info(f"BlueSky: Uploaded {image_path}")
        except Exception as e:
            logger.error(f"BlueSky: Failed to upload media {image_path}. Error: {e}")
            continue

    return image_blobs


def detect_facets(text):
    """Detect URLs and hashtags in text and create facets for them."""
    facets = []

    # URL pattern
    url_pattern = r"https?://[^\s]+"
    # Hashtag pattern - matches # followed by word chars (excluding spaces)
    hashtag_pattern = r"#[\w]+"

    # Process URLs
    for match in re.finditer(url_pattern, text):
        start = len(text[: match.start()].encode("utf-8"))
        end = len(text[: match.end()].encode("utf-8"))
        url = text[match.start() : match.end()]

        facet = {
            "index": {"byteStart": start, "byteEnd": end},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}],
        }
        facets.append(facet)

    # Process hashtags
    for match in re.finditer(hashtag_pattern, text):
        start = len(text[: match.start()].encode("utf-8"))
        end = len(text[: match.end()].encode("utf-8"))
        tag = text[match.start() + 1 : match.end()]  # Remove the # symbol

        facet = {
            "index": {"byteStart": start, "byteEnd": end},
            "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": tag}],
        }
        facets.append(facet)

    return facets if facets else None


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
    message_list=None,
):
    """tweet the new results with title and link and pictures taking care of length limitations."""
    # type_hashtag: title (identifier) link conf_hashtags
    logger.info("Creating tweet ...")
    # https://dev.twitter.com/rest/reference/get/help/configuration
    tweet_allowed_length = 280
    if message_list is None:
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
                    return None
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
                        in_reply_to_tweet_id=previous_status_id,
                    )
                else:
                    response = twitter.create_tweet(
                        text=message,
                        in_reply_to_tweet_id=previous_status_id,
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
    message_list=None,
):
    """toot the new results with title and link and pictures taking care of length limitations."""
    # type_hashtag: title (identifier) link conf_hashtags
    logger.info("Creating toot ...")
    toot_allowed_length = 500
    if message_list is None:
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
    message_list=None,
):
    """Post a Bluesky thread once, returning the root post reference.

    Publication retries are deliberately handled by the caller after a public
    account preflight. Retrying here after an ambiguous response can create an
    exact duplicate root post.
    """
    if (
        not bluesky_client
        or BlueskyClient is None
        or atproto_models is None
        or BlueskyAtpApiError is None
    ):
        logger.error("BlueSky client or models not available. Skipping skeet.")
        return None

    if message_list is None:
        message_list = split_text(
            type_hashtag,
            title,
            identifier,
            link,
            conf_hashtags,
            phys_hashtags,
            300,
            bot_handle,
        )

    logger.info("Creating skeet ...")
    root_response = None

    for i, message_text in enumerate(message_list):
        logger.info(f"Skeet part {i + 1}: {message_text}")
        logger.debug(f"Length: {len(message_text)}")

        # Create facets for URLs
        facets = detect_facets(message_text)

        embed_to_post = None
        if i == 0 and image_blobs:  # Only add media to the first skeet of a thread
            if len(image_blobs) == 1 and isinstance(
                image_blobs[0], atproto_models.AppBskyEmbedVideo.Main
            ):
                # Handle video embed
                embed_to_post = image_blobs[0]
                logger.info(f"Using video embed for skeet, {embed_to_post=}")
            else:
                # Handle image embeds
                valid_image_objects = []
                if isinstance(image_blobs, list):
                    for blob_item in image_blobs:
                        if isinstance(
                            blob_item, atproto_models.AppBskyEmbedImages.Image
                        ):
                            valid_image_objects.append(blob_item)
                        else:
                            logger.warning(
                                f"Skipping invalid image item: {type(blob_item)}"
                            )

                if valid_image_objects:
                    embed_to_post = atproto_models.AppBskyEmbedImages.Main(
                        images=valid_image_objects
                    )
                    logger.info("Using image embed(s) for skeet")
                elif image_blobs:
                    logger.warning("No valid image objects found for embedding.")

        reply_ref = None
        if previous_skeet_ref and root_skeet_ref:
            reply_ref = atproto_models.AppBskyFeedPost.ReplyRef(
                parent=previous_skeet_ref, root=root_skeet_ref
            )

        try:
            # Construct the record for the post with facets
            post_record = atproto_models.AppBskyFeedPost.Record(
                text=message_text,
                facets=facets,  # Add URL facets
                created_at=bluesky_client.get_current_time_iso(),
                embed=embed_to_post if i == 0 else None,
                reply=reply_ref,
            )

            # Prepare data for create_record
            record_data = atproto_models.ComAtprotoRepoCreateRecord.Data(  # pyright: ignore [reportOptionalMemberAccess]
                repo=bluesky_client.me.did,  # pyright: ignore [reportOptionalMemberAccess, reportUnknownMemberType]
                collection=atproto_models.ids.AppBskyFeedPost,  # pyright: ignore [reportOptionalMemberAccess]
                record=post_record.model_dump(
                    exclude_none=True
                ),  # Convert record to dict
            )

            response = bluesky_client.com.atproto.repo.create_record(data=record_data)  # pyright: ignore [reportOptionalMemberAccess, reportUnknownMemberType]

            logger.debug(f"Skeet part {i + 1} response: {response}")
            current_skeet_strong_ref = atproto_models.create_strong_ref(response)  # pyright: ignore [reportOptionalMemberAccess]

            if root_response is None:
                root_response = {"uri": response.uri, "cid": response.cid}  # pyright: ignore [reportOptionalMemberAccess, reportAttributeAccessIssue]

            if i == 0:  # If this is the first skeet
                root_skeet_ref = current_skeet_strong_ref  # It becomes the root for subsequent replies
            previous_skeet_ref = (
                current_skeet_strong_ref  # Current skeet becomes parent for the next
            )

        except BlueskyAtpApiError as exception:  # pyright: ignore [reportPossiblyUnboundVariable]
            logger.error("BlueSky API error during skeet part %d: %s", i + 1, exception)
            return None
        except Exception as exception:
            logger.error("Generic error during skeet part %d: %s", i + 1, exception)
            return None

        # If there are more messages, wait a bit before posting the next part of the thread
        if i < len(message_list) - 1:
            time.sleep(2)  # Short delay for threading

    return root_response


def attachment_candidates(experiment, post):
    """Classify relevant feed attachments without external metadata."""
    candidates = []
    for media in post.get("media_content", []):
        media_url = media.get("url", "")
        if not media_url:
            continue
        path = urlparse(media_url).path
        filename = Path(path).name.casefold()
        suffix = Path(path).suffix.casefold()
        kind = None
        if experiment.upper() == "CMS":
            if re.search(r"/files/.*figures?_", path, flags=re.IGNORECASE):
                kind = "figure"
        elif experiment.upper() == "ATLAS":
            if suffix in {".png", ".jpg", ".jpeg"}:
                kind = "figure"
            elif suffix == ".pdf" and not re.search(r"^fig", filename):
                kind = "document"
        elif experiment.upper() == "LHCB":
            if suffix == ".zip":
                kind = "archive"
        elif suffix in {".png", ".jpg", ".jpeg", ".pdf"} and re.search(
            r"(?:^|[_-])fig(?:ure)?", filename
        ):
            kind = "figure"
        if kind:
            candidates.append((media_url, kind))
    return candidates


def bluesky_post_url(handle, uri):
    """Build the public Bluesky URL for an AT URI."""
    record_key = str(uri).rsplit("/", 1)[-1]
    return f"https://bsky.app/profile/{handle}/post/{record_key}"


def build_argument_parser():
    """Create the command-line interface shared by local and scheduled runs."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--dry", help="perform dry run without posting", action="store_true"
    )
    parser.add_argument(
        "-v", "--verbose", help="enable verbose output", action="store_true"
    )
    parser.add_argument("-a", "--analysis", help="post a specific analysis", type=str)
    parser.add_argument(
        "-m", "--max", help="maximum number of analyses to post", type=int, default=3
    )
    parser.add_argument(
        "-k", "--keep", help="keep media directories", action="store_true"
    )
    parser.add_argument(
        "-l", "--list", help="list feed analyses, then quit", action="store_true"
    )
    parser.add_argument("-g", "--nogif", help="do not create GIF", action="store_true")
    parser.add_argument(
        "-f",
        "--figmax",
        help="maximum number of figures to use",
        type=int,
        default=20,
    )
    parser.add_argument(
        "-e", "--experiment", help="experiment to post for", type=str, default="CMS"
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
    parser.add_argument("--arXiv", help="use validated arXiv link", action="store_true")
    parser.add_argument(
        "--cover-mode",
        choices=("auto", "none"),
        default="auto",
        help="add the configured title page or branded cover",
    )
    return parser


def _load_feed_entries(config, experiment, run_summary):
    entries = []
    failed = False
    for feed_id, rss_url in config["FEED_DICT"].items():
        logger.info("Getting feed for %s", feed_id)
        feed = read_feed(rss_url, feed_id=feed_id, experiment=experiment)
        if not feed:
            logger.error("Could not read feed %s", feed_id)
            run_summary.add("feed_failed", feed_id=feed_id)
            failed = True
            continue
        feed_entries = feed.get("entries", [])
        logger.info("Found %d items", len(feed_entries))
        for entry in feed_entries:
            entry["feed_id"] = feed_id
        entries.extend(feed_entries)
    return entries, failed


def _prepare_publication_media(publication, post, maximum_figures, output_directory):
    downloaded = download_media_candidates(
        attachment_candidates(publication.experiment, post),
        output_directory / "downloads",
        experiment=publication.experiment,
        feed_id=publication.feed_id,
        identifier=publication.identifier,
    )
    figures = [path for kind, path in downloaded if kind == "figure"]
    documents = [path for kind, path in downloaded if kind == "document"]
    archives = [path for kind, path in downloaded if kind == "archive"]
    if archives:
        figures = safe_extract_lhcb_figures(
            archives[0], output_directory / "archive", maximum_figures
        )
    figures = order_media(figures)[:maximum_figures]
    return Publication(
        experiment=publication.experiment,
        feed_id=publication.feed_id,
        identifier=publication.identifier,
        title=publication.title,
        link=publication.link,
        lifecycle_stage=publication.lifecycle_stage,
        media_paths=tuple(figures),
        document_paths=tuple(documents),
    )


def _adopt_remote_delivery(publication, platform, config, ledger, run_summary):
    rendered = (
        MastodonRenderer().render(publication)
        if platform == "mastodon"
        else BlueskyRenderer().render(publication)
    )
    expected_text_hash = hashlib.sha256(
        rendered.messages[0].encode("utf-8")
    ).hexdigest()
    if platform == "mastodon":
        existing = find_existing_mastodon_post(
            config["AUTH"].get("MASTODON_BOT_HANDLE", ""),
            publication.identifier,
            publication.link,
            expected_text_hash=expected_text_hash,
        )
    else:
        existing = find_existing_bluesky_post(
            config["AUTH"].get("BLUESKY_HANDLE", ""),
            publication.identifier,
            publication.link,
            expected_text_hash=expected_text_hash,
        )
    if not existing:
        return False
    post_id, post_url = existing
    ledger.mark(
        publication,
        platform,
        post_id=post_id,
        post_url=post_url,
        adopted=True,
    )
    run_summary.add(
        "adopted",
        platform=platform,
        identifier=publication.identifier,
        post_url=post_url,
    )
    logger.info("Adopted existing %s post %s", platform, post_url)
    return True


def main():
    """Publish normalized feed entries with shared media and durable state."""
    args = build_argument_parser().parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    maximum_posts = 1 if args.analysis else args.max
    experiment = args.experiment
    config = load_config(experiment, args.config, args.auth)
    ledger = DeliveryLedger(Path("delivery-ledger"), experiment)
    migrated = ledger.migrate_legacy(Path.cwd())
    if migrated:
        logger.info("Migrated %d legacy delivery records", migrated)
    run_summary = RunSummary(experiment=experiment)

    def write_run_summary():
        with open("run-summary.json", "w", encoding="utf-8") as summary_file:
            json.dump(
                {"experiment": experiment, "events": run_summary.events},
                summary_file,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            summary_file.write("\n")

    atexit.register(write_run_summary)
    feed_entries, feed_failed = _load_feed_entries(config, experiment, run_summary)
    if args.list:
        for post in sorted(
            feed_entries,
            key=lambda item: (
                item["feed_id"],
                maya.parse(item["published"]).datetime(),
            ),
        ):
            logger.info(
                " - %s (%s), published %s",
                post["dc_source"],
                post["feed_id"],
                post["published"],
            )
        if feed_failed:
            raise SystemExit(1)
        return

    twitter_client = twitter_auth(config["AUTH"])
    mastodon_client = mastodon_auth(config["AUTH"])
    bluesky_client = bluesky_auth(config["AUTH"])
    required_platforms = []
    if twitter_client:
        required_platforms.append("twitter")
    if mastodon_client:
        required_platforms.append("mastodon")
    if bluesky_client:
        required_platforms.append("bluesky")
    if "BLUESKY_HANDLE" in config["AUTH"] and not bluesky_client:
        run_summary.add("failed", platform="bluesky", reason="authentication")
        required_platforms.append("bluesky")

    posted_count = 0
    for post in sorted(
        feed_entries, key=lambda item: maya.parse(item["published"]).datetime()
    ):
        identifier = post["dc_source"]
        malformed_pas = re.match(
            r"(CMS-PAS-).{3}-([A-Z]{3}-\d{2}-\d{3})-.*", identifier
        )
        if malformed_pas:
            identifier = malformed_pas.group(1) + malformed_pas.group(2)
        if args.analysis and args.analysis not in identifier:
            continue

        arxiv_link = None
        if identifier.startswith("arXiv"):
            arxiv_id = identifier.rsplit(":", 1)[-1]
            candidate_link = f"https://arxiv.org/abs/{arxiv_id}"
            response = request_with_retries(
                candidate_link,
                phase="arXiv validation",
                experiment=experiment,
                identifier=identifier,
            )
            if response is not None:
                if response.status_code < 400:
                    arxiv_link = candidate_link
                response.close()
        link = arxiv_link if args.arXiv and arxiv_link else post.link
        publication = Publication(
            experiment=experiment,
            feed_id=post["feed_id"],
            identifier=identifier,
            title=format_title(post.title),
            link=link,
            lifecycle_stage=lifecycle_stage_for(identifier),
        )

        enabled = {
            "twitter": bool(twitter_client),
            "mastodon": bool(mastodon_client),
            "bluesky": bool(bluesky_client),
        }
        deliver = {}
        for platform, is_enabled in enabled.items():
            if not is_enabled:
                deliver[platform] = False
                continue
            deliver[platform] = bool(
                args.analysis or not ledger.delivered(publication, platform)
            )
            if (
                deliver[platform]
                and not args.analysis
                and not args.dry
                and platform in {"mastodon", "bluesky"}
                and _adopt_remote_delivery(
                    publication, platform, config, ledger, run_summary
                )
            ):
                deliver[platform] = False
        if not any(deliver.values()):
            continue

        output_directory = Path(identifier.replace(":", "_"))
        publication = _prepare_publication_media(
            publication, post, args.figmax, output_directory
        )
        media = prepare_media_sequence(
            publication,
            output_directory / "prepared",
            create_animation=not args.nogif,
            cover_mode=args.cover_mode,
        )
        mastodon_rendered = MastodonRenderer().render(publication)
        bluesky_rendered = BlueskyRenderer().render(publication)
        twitter_rendered = render_messages(publication, 280)
        logger.info("Prepared alt text: %s", media.alt_text)
        run_summary.add(
            "prepared",
            identifier=identifier,
            figure_count=len(media.plot_paths),
            cover=bool(media.cover_path),
            gif=bool(media.gif_path),
            mp4=bool(media.mp4_path),
        )

        twitter_media_ids = []
        mastodon_media_ids = []
        bluesky_media = []
        mastodon_uses_gif = bool(media.gif_path)
        twitter_uses_gif = bool(media.gif_path)
        if not args.dry:
            if deliver["twitter"]:
                paths = [media.gif_path] if media.gif_path else list(media.static_paths)
                if paths:
                    try:
                        twitter_media_ids = twitter_upload_images(
                            twitter_client["v1"],
                            [str(path) for path in paths],
                            twitter_uses_gif,
                        )
                    except Exception as exception:  # pylint: disable=broad-except
                        logger.error("Twitter media upload failed: %s", exception)
            if deliver["mastodon"]:
                paths = [media.gif_path] if media.gif_path else list(media.static_paths)
                if paths:
                    try:
                        mastodon_media_ids = mastodon_upload_images(
                            mastodon_client,
                            [str(path) for path in paths],
                            mastodon_uses_gif,
                            alt_text=media.alt_text,
                        )
                    except mastodon.MastodonError as exception:
                        logger.error("Mastodon media upload failed: %s", exception)
                        run_summary.add(
                            "media_failed",
                            platform="mastodon",
                            identifier=identifier,
                            reason=exception,
                        )
            if deliver["bluesky"]:
                paths = [media.mp4_path] if media.mp4_path else list(media.static_paths)
                if paths:
                    bluesky_media = bluesky_upload_media(
                        bluesky_client,
                        [str(path) for path in paths],
                        identifier,
                        alt_text=media.alt_text,
                    )

        if deliver["twitter"]:
            if args.dry:
                for message in twitter_rendered.messages:
                    logger.info("Twitter dry run: %s", message)
                run_summary.add("dry_run", platform="twitter", identifier=identifier)
            else:
                response = tweet(
                    twitter_client["v2"],
                    "",
                    publication.title,
                    identifier,
                    link,
                    "",
                    "",
                    twitter_media_ids,
                    twitter_uses_gif,
                    config["AUTH"].get("BOT_HANDLE", ""),
                    message_list=twitter_rendered.messages,
                )
                if response:
                    post_id = str(response_value(response, "id"))
                    ledger.mark(
                        publication,
                        "twitter",
                        post_id=post_id,
                        content_hash=twitter_rendered.content_hash,
                    )
                    run_summary.add("posted", platform="twitter", identifier=identifier)
                else:
                    run_summary.add("failed", platform="twitter", identifier=identifier)

        if deliver["mastodon"]:
            if args.dry:
                for message in mastodon_rendered.messages:
                    logger.info("Mastodon dry run: %s", message)
                run_summary.add("dry_run", platform="mastodon", identifier=identifier)
            else:
                response = toot(
                    mastodon_client,
                    "",
                    publication.title,
                    identifier,
                    link,
                    "",
                    "",
                    mastodon_media_ids,
                    mastodon_uses_gif,
                    config["AUTH"].get("MASTODON_BOT_HANDLE", ""),
                    message_list=mastodon_rendered.messages,
                )
                if response:
                    post_id = str(response_value(response, "id"))
                    post_url = str(response_value(response, "url"))
                    ledger.mark(
                        publication,
                        "mastodon",
                        post_id=post_id,
                        post_url=post_url,
                        content_hash=mastodon_rendered.content_hash,
                    )
                    run_summary.add(
                        "posted",
                        platform="mastodon",
                        identifier=identifier,
                        post_url=post_url,
                    )
                elif not _adopt_remote_delivery(
                    publication, "mastodon", config, ledger, run_summary
                ):
                    run_summary.add(
                        "failed", platform="mastodon", identifier=identifier
                    )

        if deliver["bluesky"]:
            if args.dry:
                for message in bluesky_rendered.messages:
                    logger.info("Bluesky dry run: %s", message)
                run_summary.add("dry_run", platform="bluesky", identifier=identifier)
            else:
                response = skeet(
                    bluesky_client,
                    "",
                    publication.title,
                    identifier,
                    link,
                    "",
                    "",
                    bluesky_media,
                    config["AUTH"].get("BLUESKY_HANDLE", ""),
                    message_list=bluesky_rendered.messages,
                )
                if response:
                    post_uri = str(response.get("uri", ""))
                    post_url = bluesky_post_url(
                        config["AUTH"].get("BLUESKY_HANDLE", ""), post_uri
                    )
                    ledger.mark(
                        publication,
                        "bluesky",
                        post_id=post_uri,
                        post_url=post_url,
                        content_hash=bluesky_rendered.content_hash,
                    )
                    run_summary.add(
                        "posted",
                        platform="bluesky",
                        identifier=identifier,
                        post_url=post_url,
                    )
                elif not _adopt_remote_delivery(
                    publication, "bluesky", config, ledger, run_summary
                ):
                    run_summary.add("failed", platform="bluesky", identifier=identifier)

        posted_count += 1
        if not args.keep:
            shutil.rmtree(output_directory, ignore_errors=True)
        if posted_count >= maximum_posts:
            break

    write_run_summary()
    if feed_failed or run_summary.required_failures(required_platforms):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
