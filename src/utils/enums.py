"""
List of useful enumerations
"""
from enum import Enum, unique


@unique
class PageId(Enum):
    TIKTOK = 177659
    FACEBOOK = 17100
    TWITTER = 163415
    MESSENGER = 19100
    INSTAGRAM = 163413
    YOUTUBE = (17101, 53175)
    GMAIL = 178151
    LINKEDIN = 163414
    AUDIENCE_NETWORK = 169721


@unique
class ZoneId(Enum):
    FEED = 1
    SIDE = 2
    STORY = 5
    WATCH = 6
    DISCOVER = 7
    SPLASH = 9
    HOMEPAGE_AD = 10
    PROMOTED_SPARKLES = 11
    COMPACT_VIDEO_YT = 12
    INVIDEOBANNER = 13
    PREROLL = 14


@unique
class DeviceId(Enum):
    DESKTOP = 1
    MOBILE = 2


@unique
class AppType(Enum):
    BROWSER = 2
    APP = 1


@unique
class Status(Enum):
    INACTIVE = 0
    ACTIVE = 1
    SUSPENDED = 2
    BLOCKED = 3
