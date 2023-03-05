import json
from pathlib import Path

from generators.YahooJpGenerator import YahooJpGenerator

if __name__ == '__main__':
    with open(Path('__file__').parent / 'channels.json', 'r') as channels_conf_file:
        channels_conf = json.load(channels_conf_file)

    output_dir = Path('__file__').parent / 'epg'
    icon_url_prefix = 'https://raw.githubusercontent.com/cloventt/epgxml/main/icons/'

    generators = [
        YahooJpGenerator(channels_conf, output_dir=output_dir, icon_url_prefix=icon_url_prefix)
    ]
