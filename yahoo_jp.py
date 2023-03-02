#
# Convert a Yahoo JP EPG into EPGXML for use with Jellyfin
# Copyright David Palmer 2023
#
import datetime
import json
import logging
import sys
import time
from pathlib import Path
import xml.etree.ElementTree as ET

import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

AREA_CODES = {
    'tokyo': '23',
    'kyoto': '41'
}

CHANNEL_IDS = {
    # map from network ID + service ID to my ID
    '0x00040x0065': 'cloventt-jp-nhkbs1',
    '0x00040x0067': 'cloventt-jp-nhkbsp',
    '0x00040x008D': 'cloventt-jp-bsnippontv',
    '0x00040x0097': 'cloventt-jp-bsasahi',
    '0x00040x00A1': 'cloventt-jp-bstbs',
    '0x00040x00AB': 'cloventt-jp-bstvtokyo',
    '0x00040x00B5': 'cloventt-jp-bsfujitv',
    '0x7E870x5C3A': 'cloventt-jp-tokyomx',
    '0x7FD20x0810': 'cloventt-jp-mbs',
    '0x7FE00x0400': 'cloventt-jp-nhk-g',
    '0x7FE10x0408': 'cloventt-jp-nhk-e',
    '0x7FE20x0410': 'cloventt-jp-nippontv1',
    '0x7FE30x0418': 'cloventt-jp-tbs1',
    '0x7FE50x0428': 'cloventt-jp-tvasahi',
    '0x7FE60x0430': 'cloventt-jp-tvtokyo',
}

ICON_URL_PREFIX = 'https://raw.githubusercontent.com/cloventt/epgxml/main/icons/'


def format_date(ts: int):
    """
    >>> format_date(1677725280)
    '20230302024800 +0000'

    :param ts: the timestamp to format (unix, seconds since 1970 UTC)
    :return: the XMLTV formatted datetime
    """
    return datetime.datetime.utcfromtimestamp(ts).strftime('%Y%m%d%H%M%S ') + '+0000'


def get_channel(network_id: str, service_id: str):
    return CHANNEL_IDS.get(network_id + service_id, None)


def get_titles(programme_conf: dict):
    api_p_title = programme_conf.get('programTitle', None)
    api_title = programme_conf.get('title', None)
    if not api_title and not api_p_title:
        raise Exception("Couldn't find a title for program", programme_conf)
    if not api_p_title:
        return api_title, None
    if not api_title:
        return api_p_title, None
    return api_p_title, api_title


def convert():
    with open(Path('__file__').parent / 'channels.json', 'r') as channels_conf_file:
        channels_conf = json.load(channels_conf_file)

    root = ET.Element('tv')

    m3u_str = '#EXTM3U\n#EXT-X-VERSION:4\n'
    for _, c in channels_conf.items():
        channel = ET.SubElement(root, 'channel', {'id': c['id']})
        for lang, dn in c['display-name'].items():
            e = ET.SubElement(channel, 'display-name', {'lang': lang})
            e.text = dn
        ET.SubElement(channel, 'icon', {'src': ICON_URL_PREFIX + c['icon']})

        if 'streamUrl' in c:
            m3u_str += f"#EXTINF:-1 tvg-logo=\"{ICON_URL_PREFIX + c['icon']}\",{c['display-name']['en']}\n"
            m3u_str += f"{c['streamUrl']}\n\n"

    logger.info("Created channel config elements")
    logger.info("Writing out the m3u file")
    with open(Path('__file__').parent / 'cloventt.jp.m3u8', 'w') as m3u:
        m3u.write(m3u_str)

    start_time = int(time.time()) - (int(time.time()) % 60)
    params = [
        {
            'siTypeId': 3,
            'areaId': 23,
            'hours': '48',
            'broadCastStartDate': start_time,
            'channelNumber': "",
            '_api': 'programListingQuery'
        },
        {
            'siTypeId': 3,
            'areaId': 41,
            'hours': '72',
            'broadCastStartDate': start_time,
            'channelNumber': "",
            '_api': 'programListingQuery'
        },
        {
            'siTypeId': 1,
            'areaId': 23,
            'hours': '96',
            'broadCastStartDate': start_time,
            'channelNumber': "101 103 141 151 161 171 181",
            '_api': 'programListingQuery'
        },
    ]
    for param in params:
        processed = 0
        logger.info("Getting programmes for channel: %s", param)
        req = requests.get(
            'https://tv.yahoo.co.jp/api/adapter',
            params=param)

        logger.info("Requesting endpoint: %s", req.url)
        req.raise_for_status()

        req_json = req.json()
        logger.debug(json.dumps(req_json, indent=2))
        logging.info("Expect these results: %s", req_json['ResultSet']['attribute'])
        for p in req_json['ResultSet']["Result"]:
            channel = get_channel(p['networkId'], p['serviceId'])
            if channel is not None:
                programme = ET.SubElement(root,
                                          'programme',
                                          {
                                              'channel': channel,
                                              'start': format_date(p['broadCastStartDate']),
                                              'stop': format_date(p['broadCastEndDate']),
                                          }
                                          )
                title, subtitle = get_titles(p)
                title_e = ET.SubElement(programme, 'title', {'lang': 'jp'})
                title_e.text = title
                if subtitle:
                    subtitle_e = ET.SubElement(programme, 'sub-title', {'lang': 'jp'})
                    subtitle_e.text = subtitle
                if 'summary' in p:
                    desc = ET.SubElement(programme, 'desc', {'lang': 'jp'})
                    desc.text = p.get('summary')
                image = p.get("featureImage", None)
                if image:
                    image_e = ET.SubElement(programme, 'icon')
                    image_e.text = image
                processed += 1
        logging.info("Added %s programmes for channel", processed)

    with open(Path('__file__').parent / 'cloventt.jp.epg.xml', 'wb') as epgxml:
        ET.indent(root)
        data = ET.tostring(root, encoding='utf-8')
        epgxml.write(data)


if __name__ == '__main__':
    convert()
