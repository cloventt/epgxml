import dataclasses
import datetime
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import List, Union

from epglib.types import MultiLingualString, Image


@dataclasses.dataclass
class XMLTVProgramme:
    channel_id: str
    title: MultiLingualString
    sub_title: MultiLingualString
    description: MultiLingualString
    categories: List[MultiLingualString]
    start: datetime
    stop: datetime
    icon: Union[str, Image]
    images: List[Union[str, Image]]

    def append_to_tree(self, epg: ET.Element):
        node = ET.SubElement(epg, 'programme', {
            'channel': self.channel_id,
            'start': XMLTVProgramme.format_date(self.start),
            'stop': XMLTVProgramme.format_date(self.stop),
        })

        for lang, title in self.title.items():
            n = ET.SubElement(node, 'title', {'lang': lang})
            n.text = title

        for lang, sub_title in self.sub_title.items():
            n = ET.SubElement(node, 'sub-title', {'lang': lang})
            n.text = sub_title

        for lang, desc in self.sub_title.items():
            n = ET.SubElement(node, 'desc', {'lang': lang})
            n.text = desc

        for category in self.categories:
            for lang, cat in category.items():
                n = ET.SubElement(node, 'category', {'lang': lang})
                n.text = cat

        if self.icon:
            if type(self.icon) == 'str':
                ET.SubElement(node, 'icon', {'src': self.icon})
            else:
                ET.SubElement(node, 'icon', {
                    'src': self.icon.get('url'),
                    'height': self.icon.get('height'),
                    'width': self.icon.get('width')
                })

    @staticmethod
    def format_date(date: datetime) -> str:
        """
            Formats a datetime object into the "ISO-8601 - inspired"
            format used by XMLTV spec.

            >>> XMLTVProgramme.format_date(datetime.utcfromtimestamp(1677725280))
            '20230302024800 +0000'
            >>> XMLTVProgramme.format_date(datetime.fromtimestamp(1677725280, tz=timezone(timedelta(hours=13))))
            '20230302154800 +1300'

            :param date: the datetime object to format
            :return: the XMLTV-formatted datetime
            """
        return date.strftime('%Y%m%d%H%M%S ') + (date.strftime('%z') or '+0000')
