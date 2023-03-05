import logging
import sys
from abc import abstractmethod
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

    @property
    @abstractmethod
    def name(self):
        pass

    def __init__(self,
                 channels_conf: dict[str, ChannelConf],
                 output_dir: Path,
                 icon_url_prefix: str = 'https://raw.githubusercontent.com/cloventt/epgxml/main/icons/'
                 ):
        self.logger = logging.getLogger('EpgGenerator:' + self.name)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.output_dir = output_dir
        self.icon_url_prefix = icon_url_prefix

        relevant_channels = {}
        for (k, v) in channels_conf.items():
            if v['epgSource'] == self.name:
                relevant_channels['k'] = v
        channels, programmes = self.scrape(relevant_channels)
        self.write(channels, programmes)
        pass

    def scrape(self, channel_conf: dict) -> tuple[List[XMLTVChannel], List[XMLTVProgramme]]:
        raise NotImplementedError()

    def write(self, channels: List[XMLTVChannel], programmes: List[XMLTVProgramme]):
        with open(self.output_dir / (self.name + '.epg.xml'), 'wb') as out_file:
            root = ET.Element('tv')
            for channel in channels:
                channel.append_to_tree(root, self.icon_url_prefix)

            for programme in programmes:
                programme.append_to_tree(root)

            xml_headers = [s.encode('utf-8') for s in [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<!DOCTYPE tv SYSTEM "xmltv.dtd">'
            ]]

            out_file.writelines(xml_headers)

            ET.indent(root)
            epg = ET.tostring(root, encoding='utf-8')
            out_file.write(epg)




