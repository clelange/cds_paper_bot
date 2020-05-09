# CDS Paper Bot

[![DOI](https://zenodo.org/badge/100429308.svg)](https://doi.org/10.5281/zenodo.1203624)

This is a Twitter bot written in python (version 3) that reads the RSS feeds of the [CERN Document Server (CDS)](https://cds.cern.ch/) and creates tweets of new publications.

It currently works pretty well for the ATLAS and CMS feeds listed in [`feeds.ini`](../blob/master/feeds.ini), could probably easily be extended to the LHCb and ALICE ones listed in the file already.

Follow the bots on twitter [@CMSpapers](https://twitter.com/CMSpapers), [@ATLASpapers](https://twitter.com/ATLASpapers)/[@ATLAS_results](https://twitter.com/ATLAS_results), and [@LHCb_results](https://twitter.com/LHCb_results).

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

For information on running the bot, do

```shell
python cds_paper_bot.py --help
```

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
