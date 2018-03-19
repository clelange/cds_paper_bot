[![DOI](https://zenodo.org/badge/100429308.svg)](https://zenodo.org/badge/latestdoi/100429308)

# CDS Paper Bot

This is a Twitter bot written in python (version 3) that reads the RSS feeds of the [CERN Document Server (CDS)](https://cds.cern.ch/) and creates tweets of new publications.

It currently works pretty well for the ATLAS and CMS feeds listed in [`feeds.ini`](../blob/master/feeds.ini), could probably easily be extended to the LHCb and ALICE ones listed in the file already.

Follow the bots on twitter [@CMS_results](https://twitter.com/CMS_results) and [@ATLAS_results](https://twitter.com/ATLAS_results).

To get it to work as a bot, an `auth.ini` file containing information in the following format:
```
[CMS]
BOT_HANDLE = @CMS_results
CONSUMER_KEY = xxxxxxxxxxxxxxxxxxxxxxxxx
CONSUMER_SECRET = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ACCESS_TOKEN = xxxxxxxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ACCESS_TOKEN_SECRET = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
For more details on authentication, refer to the [Twitter Developer Platform](https://developer.twitter.com/).

For information on running the bot, do
```
python cds_paper_bot.py --help
```
