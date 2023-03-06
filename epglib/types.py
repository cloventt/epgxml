import dataclasses

from typing import TypedDict


class MultiLingualString(TypedDict, total=False):
    """
    Strings that can have multiple languages are represented
    by a dict with keys for each ISO-639-2 language code
    required.
    """
    en: str
    jp: str
    de: str


class Image(TypedDict):
    """
    Strings that can have multiple languages are represented
    by a dict with keys for each ISO-639-2 language code
    required.
    """
    url: str
    height: int
    width: int


class ChannelConf(TypedDict, total=False):
    """
    Schema for the channels.json config file.
    """
    id: str
    display_name: MultiLingualString
    icon: str
    epgSource: str

    channelNumber: int
    channelArea: str

