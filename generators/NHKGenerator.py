import json
from pathlib import Path
from typing import List

from epglib.EpgGenerator import EpgGenerator
from epglib.XMLTVChannel import XMLTVChannel
from epglib.XMLTVProgramme import XMLTVProgramme

import requests
import pendulum

from epglib.types import Image

CHANNEL_MAP = {
    'g1': 'cloventt-jp-nhk-g',
    'e1': 'cloventt-jp-nhk-e',
    's1': 'cloventt-jp-nhk-bs1',
    's3': 'cloventt-jp-nhk-bsp',
}

TITLE_OVERRIDES = [
    # these are names that aren't reliably found in keywords
    'ＮＨＫニュース　おはよう日本'
]


class NHKGenerator(EpgGenerator):
    name = 'nhk-japan'

    def scrape(self, channel_conf: dict) -> tuple[List[XMLTVChannel], List[XMLTVProgramme]]:
        days_to_scrape = self._get_days_to_scrape(pendulum.now())
        self.logger.info("Requesting data for the following days: %s", days_to_scrape)
        programmes = []
        for day in days_to_scrape:
            self.logger.info("Requesting data for %s", day)
            req = requests.get('https://api.nhk.or.jp/r5/pg2/list/4/130/g1/' + day + '.json')
            req.raise_for_status()
            response = req.json()
            self.logger.debug("Received raw API response: %s", response)
            for service, shows in response.get("list", dict()).items():
                if service in CHANNEL_MAP:
                    for show in shows:
                        start_time = pendulum.parse(show.get('start_time'))
                        end_time = pendulum.parse(show.get('end_time'))

                        og_title = show.get("title")
                        # NHK don't include the program title on its own for some reason,
                        # they always append on some extra info. This is useless for people
                        # who want to DVR every episode of a series for example - we need a
                        # stable name. Luckily they nearly always include the title in the
                        # "keywords" section
                        keywords = show.get("keywords")
                        keywords = sorted(keywords, key=len) + TITLE_OVERRIDES  # always grab the longest match
                        title = og_title
                        for keyword in keywords:
                            if keyword in og_title and keyword != og_title:
                                title = keyword
                        subtitle = show.get("subtitle")
                        description = show.get("content")
                        for genre in show.get("genre"):
                            major = hex(int(genre[:2]))
                            minor = hex(int(genre[2:]))
                        icon_conf = show.get("images").get("logo_l")
                        if icon_conf.get("url"):
                            icon = Image(url=icon_conf.get("url"),
                                         height=icon_conf.get("height"),
                                         width=icon_conf.get("width")
                                         )
                        else:
                            icon = None

                        images = []
                        thumb_conf = show.get("images").get("thumbnail_m")
                        if thumb_conf.get("url"):
                            images.append(Image(url=thumb_conf.get("url"),
                                                height=thumb_conf.get("height"),
                                                width=thumb_conf.get("width")
                                                ))

                        more_images = show.get('extra', {}).get('pr_images', [])
                        for image in more_images:
                            for k, conf in image.items():
                                if type(conf) == 'dict':
                                    if conf.get("url"):
                                        images.append(Image(url=conf.get("url"),
                                                            height=conf.get("height"),
                                                            width=conf.get("width")
                                                            ))

                        new_programme = XMLTVProgramme(channel_id=CHANNEL_MAP[service], title={'jp': title},
                                                       sub_title={'jp': subtitle} if subtitle else {},
                                                       description={'jp': description} if description else {},
                                                       categories=[], start=start_time, stop=end_time, icon=icon,
                                                       images=images, )
                        self.logger.info("Adding programme: %s", new_programme)
                        programmes.append(new_programme)
        return [], programmes

    @staticmethod
    def _get_days_to_scrape(current_time: pendulum, days: int = 7) -> List[str]:
        """
        Get a list of days to attempt to scrape. The API expects ISO-8601 dates as filenames
        when making the request.

        Whatever time is passsed to the method will be converted to Japanese time. This is because
        the programming schedule is in Japanese time, and we don't want to request the previous
        day's schedule in the hours between midnight Japanese time and midnight UTC, for example.
        >>> NHKGenerator._get_days_to_scrape(pendulum.parse('2023-03-05T22:35:00+00:00'), days=1)
        ['2023-03-06']
        >>> NHKGenerator._get_days_to_scrape(pendulum.parse('2023-03-06T22:35:00+09:00'), days=1)
        ['2023-03-06']
        >>> NHKGenerator._get_days_to_scrape(pendulum.parse('2023-03-06T04:35:00+13:00'), days=1)
        ['2023-03-06']

        You can also specify an arbitrary number of days to request from their API.
        >>> NHKGenerator._get_days_to_scrape(pendulum.parse('2023-03-05T22:35:00+00:00'), days=7)
        ['2023-03-06', '2023-03-07', '2023-03-08', '2023-03-09', '2023-03-10', '2023-03-11', '2023-03-12']


        :param current_time: current time as milliseconds since epoch
        :param days: days to get
        :return: list of correctly formatted dates to request from the API
        """
        res = []
        japan_time = current_time.in_timezone('Asia/Tokyo')
        for i in range(0, days):
            res.append(japan_time.add(days=i).to_iso8601_string()[:10])
        return res


if __name__ == '__main__':
    with open(Path('__file__').parent / '..' / 'channels.json', 'r') as channels_conf_file:
        channels_conf = json.load(channels_conf_file)

    output_dir = Path('__file__').parent / '..' / 'epg'

    NHKGenerator(channels_conf, output_dir)
