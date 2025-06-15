# CDS Paper Bot

[![DOI](https://zenodo.org/badge/100429308.svg)](https://doi.org/10.5281/zenodo.1203624)

This is a bot written in python (version 3) that reads the RSS feeds of the [CERN Document Server (CDS)](https://cds.cern.ch/) and creates tweets/toots/skeets of new publications.

It currently works pretty well for the ATLAS and CMS feeds listed in [`feeds.ini`](../blob/master/feeds.ini), and without images also for LHCb and ALICE.

Follow the bots on X:

- [@CMSpapers](https://x.com/CMSpapers)
- [@ATLASpapers](https://x.com/ATLASpapers)
- [@LHCb_results](https://twitter.com/LHCb_results)

Follow on Mastodon:

- [@cmspapers@mastodon.social](https://mastodon.social/@CMSpapers)

Follow on BlueSky:

- [@cmspapers.bsky.social](https://bsky.app/profile/cmspapers.bsky.social)

To get it to work as a bot, an `auth.ini` file containing information in the following format:

```ini
[CMS]
BOT_HANDLE = @CMS_results
CONSUMER_KEY = xxxxxxxxxxxxxxxxxxxxxxxxx
CONSUMER_SECRET = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ACCESS_TOKEN = xxxxxxxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ACCESS_TOKEN_SECRET = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

For more details on authentication, refer to the [Twitter Developer Platform](https://developer.twitter.com/).

For using the tool with a Mastodon bot, `auth.ini` should contain:

```ini
[CMS]
MASTODON_BOT_HANDLE = @CMSpapers@mastodon.social
MASTODON_ACCESS_TOKEN = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

You can obtain the access token by creating a new application on your Mastodon account's
[application settings](https://mastodon.social/settings/applications)
(here provided for [mastodon.social](https://mastodon.social/)).

For using the tool with a BlueSky bot, `auth.ini` should contain:

```ini
[CMS]
BLUESKY_HANDLE = @cmspapers.bsky.social
BLUESKY_APP_PASSWORD = xxxx-xxxx-xxxx-xxxx
```

where `BLUESKY_APP_PASSWORD` is the password of the app you created in [BlueSky](https://bsky.app/).

For information on running the bot, do

```shell
python cds_paper_bot.py --help
```

Note: if this doesn't work on MacOS, make sure to `brew install freetype imagemagick`
and `export MAGICK_HOME=/opt/homebrew/opt/imagemagick`.

## Docker image

If you would like to run the bot in an isolated environment, e.g. on a Raspberry Pi, you can try to use the [Dockerfile](Dockerfile).
Build the container using:

```shell
docker build -t cds_paper_bot .
```

Then run it from the repository directory:

```shell
docker run --rm -ti -v "$(pwd)":/home/app -w /home/app cds_paper_bot python cds_paper_bot.py
```

## Deploying the bot to GitLab CI/CD

Using the [CERN GitLab installation](https://gitlab.cern.ch) and its CI/CD capabilities, you can run the bot such that it regularly checks for new analyses. Follow the instructions [here](GitLabCI.md).
