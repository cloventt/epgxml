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

CATEGORIES = {
    "0x0": {"jp": "ニュース／報道", "en": "News"},
    "0x00x0": {"jp": "定時・総合"},
    "0x00x1": {"jp": "天気"},
    "0x00x2": {"jp": "特集・ドキュメント"},
    "0x00x3": {"jp": "政治・国会"},
    "0x00x4": {"jp": "経済・市況"},
    "0x00x5": {"jp": "海外・国際"},
    "0x00x6": {"jp": "解説"},
    "0x00x7": {"jp": "討論・会談"},
    "0x00x8": {"jp": "報道特番"},
    "0x00x9": {"jp": "ローカル・地域"},
    "0x00xA": {"jp": "交通"},
    "0x00xF": {"jp": "その他"},
    "0x1": {"jp": "スポーツ", "en": "Sports"},
    "0x10x0": {"jp": "スポーツニュース"},
    "0x10x6": {"jp": "オリンピック・国際大会"},
    "0x10xF": {"jp": "その他"},
    "0x2": {"jp": "情報／ワイドショー", "en": "Infotainment"},
    "0x20x0": {"jp": "芸能・ワイドショー"},
    "0x20x1": {"jp": "ファッション"},
    "0x20x2": {"jp": "暮らし・住まい"},
    "0x20x3": {"jp": "健康・医療"},
    "0x20x4": {"jp": "ショッピング・通販"},
    "0x20x5": {"jp": "グルメ・料理"},
    "0x20x6": {"jp": "イベント"},
    "0x20x7": {"jp": "番組紹介・お知らせ"},
    "0x20xF": {"jp": "その他"},
    "0x3": {"jp": "ドラマ"},
    "0x30x0": {"jp": "国内ドラマ"},
    "0x30x1": {"jp": "海外ドラマ"},
    "0x30x2": {"jp": "時代劇"},
    "0x30xF": {"jp": "その他"},
    "0x4": {"jp": "音楽"},
    "0x40x0": {"jp": "国内ロック・ポップス"},
    "0x40x1": {"jp": "海外ロック・ポップス"},
    "0x40x2": {"jp": "クラシック・オペラ"},
    "0x40x4": {"jp": "歌謡曲・演歌"},
    "0x40x5": {"jp": "ライブ・コンサート"},
    "0x40x6": {"jp": "ランキング・リクエスト"},
    "0x40x8": {"jp": "民謡・邦楽"},
    "0x40x9": {"jp": "童謡・キッズ"},
    "0x40xF": {"jp": "その他"},
    "0x5": {"jp": "バラエティ"},
    "0x50x0": {"jp": "クイズ"},
    "0x50x1": {"jp": "ゲーム"},
    "0x50x2": {"jp": "トークバラエティ"},
    "0x50x3": {"jp": "お笑い・コメディ"},
    "0x50x4": {"jp": "音楽バラエティ"},
    "0x50x5": {"jp": "旅バラエティ"},
    "0x50x6": {"jp": "料理バラエティ"},
    "0x50xF": {"jp": "その他"},
    "0x6": {"jp": "映画"},
    "0x60x0": {"jp": "洋画"},
    "0x60x1": {"jp": "邦画"},
    "0x7": {"jp": "アニメ／特撮"},
    "0x70x0": {"jp": "国内アニメ"},
    "0x70x1": {"jp": "海外アニメ"},
    "0x70xF": {"jp": "その他"},
    "0x8": {"jp": "ドキュメンタリー／教養"},
    "0x80x0": {"jp": "社会・時事"},
    "0x80x1": {"jp": "歴史・紀行"},
    "0x80x2": {"jp": "自然・動物・環境"},
    "0x80x3": {"jp": "宇宙・科学・医学"},
    "0x80x4": {"jp": "カルチャー・伝統文化"},
    "0x80x5": {"jp": "文学・文芸"},
    "0x80x7": {"jp": "ドキュメンタリー全般"},
    "0x80x8": {"jp": "インタビュー・討論"},
    "0x80xF": {"jp": "その他"},
    "0x9": {"jp": "劇場／公演"},
    "0x90x0": {"jp": "現代劇・新劇"},
    "0x90x2": {"jp": "ダンス・バレエ"},
    "0x90x4": {"jp": "歌舞伎・古典"},
    "0xA": {"jp": "趣味／教育"},
    "0xA0x0": {"jp": "旅・釣り・アウトドア"},
    "0xA0x1": {"jp": "園芸・ペット・手芸"},
    "0xA0x2": {"jp": "音楽・美術・工芸"},
    "0xA0x3": {"jp": "囲碁・将棋"},
    "0xA0x7": {"jp": "会話・語学"},
    "0xA0x8": {"jp": "幼児・小学生"},
    "0xA0x9": {"jp": "中学生・高校生"},
    "0xA0xA": {"jp": "大学生・受験"},
    "0xA0xB": {"jp": "生涯教育・資格"},
    "0xA0xC": {"jp": "教育問題"},
    "0xA0xF": {"jp": "その他"},
    "0xB": {"jp": "福祉"},
    "0xB0x0": {"jp": "高齢者"},
    "0xB0x1": {"jp": "障害者"},
    "0xB0x2": {"jp": "社会福祉"},
    "0xB0x4": {"jp": "手話"},
    "0xB0x5": {"jp": "文字(字幕)"},
    "0xB0x6": {"jp": "音声解説"},
    "0xB0xF": {"jp": "その他"},
    "0xE": {"jp": "拡張"},
    "0xE0x0": {"jp": "BS／地上デジタル放送用番組付属情報"},
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
        logger.debug(json.dumps(req_json, indent=2, ensure_ascii=False))
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
                    ET.SubElement(programme, 'icon', {'src': image})

                genres = p.get('majorGenreId', [])
                for g in genres:
                    category = CATEGORIES.get(g, None)
                    if category:
                        for lang, name in category.items():
                            cat_e = ET.SubElement(programme, 'category', {'lang': lang})
                            cat_e.text = name
                processed += 1

        logging.info("Added %s programmes for channel", processed)

    with open(Path('__file__').parent / 'cloventt.jp.epg.xml', 'wb') as epgxml:
        ET.indent(root)
        data = ET.tostring(root, encoding='utf-8')
        epgxml.write(data)


if __name__ == '__main__':
    convert()
