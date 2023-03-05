import json
import time
from datetime import datetime
from pathlib import Path
from typing import List

import requests

from epglib.EpgGenerator import EpgGenerator
from epglib.XMLTVChannel import XMLTVChannel
from epglib.XMLTVProgramme import XMLTVProgramme
from epglib.types import ChannelConf


class YahooJpGenerator(EpgGenerator):
    name = 'yahoo-japan'

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
        "0x3": {"jp": "ドラマ", "en": "Drama"},
        "0x30x0": {"jp": "国内ドラマ"},
        "0x30x1": {"jp": "海外ドラマ"},
        "0x30x2": {"jp": "時代劇"},
        "0x30xF": {"jp": "その他"},
        "0x4": {"jp": "音楽", "en": "Music"},
        "0x40x0": {"jp": "国内ロック・ポップス"},
        "0x40x1": {"jp": "海外ロック・ポップス"},
        "0x40x2": {"jp": "クラシック・オペラ"},
        "0x40x4": {"jp": "歌謡曲・演歌"},
        "0x40x5": {"jp": "ライブ・コンサート"},
        "0x40x6": {"jp": "ランキング・リクエスト"},
        "0x40x8": {"jp": "民謡・邦楽"},
        "0x40x9": {"jp": "童謡・キッズ"},
        "0x40xF": {"jp": "その他"},
        "0x5": {"jp": "バラエティ", "en": "Variety"},
        "0x50x0": {"jp": "クイズ"},
        "0x50x1": {"jp": "ゲーム"},
        "0x50x2": {"jp": "トークバラエティ"},
        "0x50x3": {"jp": "お笑い・コメディ"},
        "0x50x4": {"jp": "音楽バラエティ"},
        "0x50x5": {"jp": "旅バラエティ"},
        "0x50x6": {"jp": "料理バラエティ"},
        "0x50xF": {"jp": "その他"},
        "0x6": {"jp": "映画", "en": "Movie"},
        "0x60x0": {"jp": "洋画"},
        "0x60x1": {"jp": "邦画"},
        "0x7": {"jp": "アニメ／特撮", "en": "Animated"},
        "0x70x0": {"jp": "国内アニメ"},
        "0x70x1": {"jp": "海外アニメ"},
        "0x70xF": {"jp": "その他"},
        "0x8": {"jp": "ドキュメンタリー／教養", "en": "Educational"},
        "0x80x0": {"jp": "社会・時事"},
        "0x80x1": {"jp": "歴史・紀行"},
        "0x80x2": {"jp": "自然・動物・環境"},
        "0x80x3": {"jp": "宇宙・科学・医学"},
        "0x80x4": {"jp": "カルチャー・伝統文化"},
        "0x80x5": {"jp": "文学・文芸"},
        "0x80x6": {"jp": "スポーツ"},
        "0x80x7": {"jp": "ドキュメンタリー全般"},
        "0x80x8": {"jp": "インタビュー・討論"},
        "0x80xF": {"jp": "その他"},
        "0x9": {"jp": "劇場／公演", "en": "Theatre"},
        "0x90x0": {"jp": "現代劇・新劇"},
        "0x90x2": {"jp": "ダンス・バレエ"},
        "0x90x4": {"jp": "歌舞伎・古典"},
        "0xA": {"jp": "趣味／教育", "en": "Hobbies"},
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
        "0xB": {"jp": "福祉", "en": "Welfare"},
        "0xB0x0": {"jp": "高齢者"},
        "0xB0x1": {"jp": "障害者"},
        "0xB0x2": {"jp": "社会福祉"},
        "0xB0x4": {"jp": "手話"},
        "0xB0x5": {"jp": "文字(字幕)"},
        "0xB0x6": {"jp": "音声解説"},
        "0xB0xF": {"jp": "その他"},
        # "0xC": {"jp": "", "en": "unknown"},
        # "0xD": {"jp": "", "en": "unknown"},
        "0xE": {"jp": "拡張"},
        "0xE0x0": {"jp": "BS／地上デジタル放送用番組付属情報"},
        "0xF": {"jp": "その他", "en": "Other"},
    }

    def scrape(self, channel_conf: dict[str, ChannelConf]) -> tuple[List[XMLTVChannel], List[XMLTVProgramme]]:
        channels = []
        for channel_id, channel in channel_conf.items():
            channels.append(XMLTVChannel(id=channel_id, display_name=channel['display_name'], icon=channel['icon']))

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

        programmes = []

        for param in params:
            processed = 0
            self.logger.info("Getting programmes for channel: %s", param)
            req = requests.get(
                'https://tv.yahoo.co.jp/api/adapter',
                params=param)

            self.logger.info("Requesting endpoint: %s", req.url)
            req.raise_for_status()

            req_json = req.json()
            self.logger.debug(json.dumps(req_json, indent=2, ensure_ascii=False))
            self.logger.info("Expect these results: %s", req_json['ResultSet']['attribute'])
            for p in req_json['ResultSet']["Result"]:
                channel = self._get_channel(p['networkId'], p['serviceId'])
                if channel is not None:
                    title, subtitle = self._get_titles(p)
                    description = p.get('summary', None)
                    title = {'jp': title}
                    subtitle = {'jp': subtitle} if subtitle else {}
                    description = {'jp': description} if description else {}

                    genres = p.get('majorGenreId', [])
                    genres = set(genres)
                    categories = []
                    for cat_id in genres:
                        canonical_category_name = self.CATEGORIES.get(cat_id, None)
                        if canonical_category_name is None:
                            self.logger.warning("Got an unknown majorGenreId: %s (%s)", cat_id, p)
                        else:
                            categories.append(canonical_category_name)

                    programme = XMLTVProgramme(
                        channel_id=channel,
                        title=title,
                        sub_title=subtitle,
                        description=description,
                        start=datetime.utcfromtimestamp(p['broadCastStartDate']),
                        stop=datetime.utcfromtimestamp(p['broadCastEndDate']),
                        icon=p.get("featureImage", None),
                        categories=categories,
                    )

                    programmes.append(programme)
                    processed += 1

            self.logger.info("Added %s programmes for channel", processed)

        return channels, programmes

    def _get_channel(self, network_id: str, service_id: str):
        return self.CHANNEL_IDS.get(network_id + service_id, None)

    def _get_titles(self, programme_conf: dict):
        api_p_title = programme_conf.get('programTitle', None)
        api_title = programme_conf.get('title', None)
        if not api_title and not api_p_title:
            raise Exception("Couldn't find a title for program", programme_conf)
        if not api_p_title:
            return api_title, None
        if not api_title:
            return api_p_title, None
        return api_p_title, api_title


if __name__ == '__main__':
    with open(Path('__file__').parent / '..' / 'channels.json', 'r') as channels_conf_file:
        channels_conf = json.load(channels_conf_file)

    output_dir = Path('__file__').parent / '..' / 'epg'

    YahooJpGenerator(channels_conf, output_dir)
