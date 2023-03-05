import dataclasses
import xml.etree.ElementTree as ET

from epglib.types import MultiLingualString


@dataclasses.dataclass
class XMLTVChannel:

    id: str
    display_name: MultiLingualString
    icon: str

    def append_to_tree(self, epg: ET.Element, icon_url_prefix: str):
        node = ET.SubElement(epg, 'channel', {
            'id': self.id,
        })

        for lang, name in self.display_name.items():
            n = ET.SubElement(node, 'display-name', {'lang': lang})
            n.text = name

        ET.SubElement(node, 'icon', {'src': icon_url_prefix + self.icon})
