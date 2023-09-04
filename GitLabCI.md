# Deploying the bot to GitLab CI/CD

## Twitter credentials

Go to the [Twitter Developers](https://developer.twitter.com/apps) website and choose "Create an app". This might ask you to apply for a Twitter developer account first.

Once this is done, you need to create an app at [this site](https://developer.twitter.com/en/apps). Having successfully created the app, go to the "Keys and tokens" tab and create "Access token & access token secret. On this page, you will also see the "Consumer API keys". Note all four down for later.

## SSH key generation and registration

In order to be able to keep track of the analyses already tweeted, you need to create a new ssh key by running the following command e.g. on lxplus (do not enter a password):

```shell
ssh-keygen -t rsa -b 4096 -f cern-gitlab-ci
```

This will create two files, `cern-gitlab-ci` and `cern-gitlab-ci.pub`, the content of which will be used in the following. The public key has to be registered to your account. Go to "User Settings" -> "[SSH Keys](https://gitlab.cern.ch/profile/keys)", paste the content of `cern-gitlab-ci.pub` into the "Key" field, adjust the "Title", and click "Add key".

## General GitLab CI/CD setup

Create a new project on the [CERN GitLab instance](https://gitlab.cern.ch/projects/new). Choose the "Import project" tab and then "Repo by URL". Enter as "Git repository URL": `https://github.com/clelange/cds_paper_bot` and choose a project name.

Once created, go to your newly-created project, choose "Settings" -> "CI / CD" and expand the "Environment variables". You will need to create a number of variables:

| Variable name      | Description                                                                                              |
| ------------------ | -------------------------------------------------------------------------------------------------------- |
| `GITMAIL`          | Your email address (will be used for commits to the project)                                             |
| `GITNAME`          | Your name (will be used for commits to the project)                                                      |
| `GIT_SSH_PRIV_KEY` | Content of `cern-gitlab-ci`                                                                              |
| `REMOTE_GIT_REPO`  | URL for cloning your repository via ssh, e.g. `ssh://git@gitlab.cern.ch:7999/username/cds_paper_bot.git` |

Once this is done, go to "CI / CD" (not the one under "Settings") -> "Pipelines", click on "Run Pipeline" and then "Create pipeline". This will update your clone of the repository from the one on [Github](https://github.com/clelange/cds_paper_bot) and build a new docker container. Whenever there are changes in this repository that you would like to profit from as well, repeat this step.

## Setting up the bot

Each bot/account will need some specific settings, and the following steps will set things up such that the bot will run on a regular schedule. Go to "CI / CD" (not the one under "Settings") -> "Schedules" and create a new schedule. To run once per hour at 15 minutes past use `15 * * * *`. Choose a name and an "Interval pattern". Mind that the bot cannot run more than once per hour due to the way GitLab cron scheduling works.

Now add a couple of variables, see [feeds.ini](https://github.com/clelange/cds_paper_bot/blob/master/feeds.ini) for a list of experiments already predefined:

| Variable name           | Description                                                  |
| ----------------------- | ------------------------------------------------------------ |
| `EXPERIMENT`            | name of the experiment, e.g. `ATLAS`                         |
| `BOT_HANDLE`            | Your twitter account handle without @, e.g. `ATLAS_results`  |
| `CONSUMER_KEY`          | The Twitter "Consumer API key" generated above               |
| `CONSUMER_SECRET`       | The Twitter "Consumer API secret key" generated above        |
| `ACCESS_TOKEN`          | The Twitter "Access token" generated above                   |
| `ACCESS_TOKEN_SECRET`   | The Twitter "Access token secret" generated above            |
| `MASTODON_BOT_HANDLE`   | Your Mastodon account handle, e.g. `@cmspapers@botsin.space` |
| `MASTODON_ACCESS_TOKEN` | Mastodon app "Access token"                                  |

You can either set both Twitter/X and Mastodon values or only one of them.
