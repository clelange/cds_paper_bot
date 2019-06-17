"""Get all titles currently in the RSS feeds for testing purposes."""
import configparser
import logging
import daiquiri
from cds_paper_bot import read_feed, format_title

daiquiri.setup(level=logging.ERROR)


def load_config(feed_file):
    """Load configs into dict."""
    config_dict = {}
    config = configparser.RawConfigParser()
    # load the feed config
    config.read(feed_file)
    config_dict = {}
    for key in config:
        config_dict[key] = config[key]
    return config_dict


def main():
    """Load the feeds, print all titles in a format useful for dumping into test_format_title.py."""
    config = load_config("feeds.ini")
    # print(config)
    for experiment in config:
        for pub_type in config[experiment]:
            print(f"            # {experiment} {pub_type}")
            this_feed = read_feed(config[experiment][pub_type])
            if this_feed:
                this_feed_entries = this_feed["entries"]
                # print("Found %d items" % len(this_feed_entries))
                for entry in this_feed_entries:
                    # print(entry.dc_source)
                    input_title = entry.title.replace("\\", "\\\\")
                    formatted_title = format_title(entry.title).replace("\\", "\\\\")
                    print(
                        f'            ("{input_title}",\n            "{formatted_title}"),'
                    )
                    # print()
            # break
        # break


if __name__ == "__main__":
    main()
