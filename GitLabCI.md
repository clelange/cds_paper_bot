# Deploying the bot to GitLab CI/CD

## Platform credentials

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

Each experiment/account needs one schedule. Go to "CI / CD" (not the one under "Settings") -> "Schedules" and create it with an interval such as `*/30 * * * *`. The CMS schedule should contain both the Mastodon and Bluesky credentials so one invocation prepares the media once and delivers it to both services. Remove older per-feed or per-platform CMS schedules after the consolidated schedule has been verified.

The scheduled job uses a [GitLab resource group](https://docs.gitlab.com/ci/resource_groups/) named for the experiment. This serializes publishers for the same experiment. It also updates the checkout before running, writes successful platform deliveries independently to `delivery-ledger/<EXPERIMENT>.json`, and uploads `run-summary.json` as a job artifact. Public-account preflight checks recover a post if the previous process published it but stopped before saving the ledger.

Now add a couple of variables, see [feeds.ini](https://github.com/clelange/cds_paper_bot/blob/master/feeds.ini) for a list of experiments already predefined:

| Variable name           | Description                                                  |
| ----------------------- | ------------------------------------------------------------ |
| `EXPERIMENT`            | name of the experiment, e.g. `ATLAS`                         |
| `BOT_HANDLE`            | Your twitter account handle without @, e.g. `ATLAS_results`  |
| `CONSUMER_KEY`          | The Twitter "Consumer API key" generated above               |
| `CONSUMER_SECRET`       | The Twitter "Consumer API secret key" generated above        |
| `ACCESS_TOKEN`          | The Twitter "Access token" generated above                   |
| `ACCESS_TOKEN_SECRET`   | The Twitter "Access token secret" generated above            |
| `MASTODON_BOT_HANDLE`   | Full Mastodon account handle, e.g. `@cmspapers@mastodon.social` |
| `MASTODON_ACCESS_TOKEN` | Mastodon app "Access token"                                  |
| `BLUESKY_HANDLE`        | Bluesky account handle, e.g. `cmspapers.bsky.social`          |
| `BLUESKY_APP_PASSWORD`  | Bluesky app password (not the account password)               |

Only configured platforms are used. For the current CMS deployment, configure Mastodon and Bluesky together; Twitter/X credentials can be omitted.
