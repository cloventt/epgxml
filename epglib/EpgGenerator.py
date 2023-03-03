from pathlib import Path
from typing import List
import xml.etree.ElementTree as ET

from epglib.XMLTVChannel import XMLTVChannel
from epglib.XMLTVProgramme import XMLTVProgramme
from epglib.types import ChannelConf


class EpgGenerator:
    """
    Abstract parent class for EPG Generators. Generators should implement the #scrape() method
    to pull the data from an API.
    """

    name: str = None  # override this to change the generator name

    def __init__(self,
                 channels_conf: dict[str, ChannelConf],
                 output_dir: Path
                 ):
        self.output_dir = output_dir

        relevant_channels = dict(filter(lambda k, c:  c['epgSource'] == self.name, channels_conf.items()))
        channels, programmes = self.scrape(relevant_channels)
        self.write(channels, programmes)
        pass

    def scrape(self, channel_conf: dict) -> tuple[List[XMLTVChannel], List[XMLTVProgramme]]:
        raise NotImplementedError()

    def write(self, channels: List[XMLTVChannel], programmes: List[XMLTVProgramme]):
        with open(self.output_dir / (self.name + '.epg.xml'), 'w') as out_file:
            root = ET.Element('tv')
            for channel in channels:
                channel.append_to_tree(root)

            for programme in programmes:
                programme.append_to_tree(root)

            out_file.writelines([
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<!DOCTYPE tv SYSTEM "xmltv.dtd">'
            ])

            ET.indent(root)
            epg = ET.tostring(root, encoding='utf-8')
            out_file.write(epg)




