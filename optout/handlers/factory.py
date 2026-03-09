"""Return the right handler class for a given broker platform."""

from .generic import GenericHandler
from .beenverified import BeenVerifiedHandler
from .intelius import InteliusHandler
from .whitepages import WhitepagesHandler
from .spokeo import SpokeoHandler
from .records_removal import RecordsRemovalHandler
from .peoplefinders import PeopleFinderHandler
from .instantcheckmate import InstantCheckmateHandler

_PLATFORM_MAP = {
    "beenverified": BeenVerifiedHandler,
    "intelius": InteliusHandler,
    "whitepages": WhitepagesHandler,
    "spokeo": SpokeoHandler,
    "records_removal": RecordsRemovalHandler,
    "peoplefinders": PeopleFinderHandler,
    "instantcheckmate": InstantCheckmateHandler,
    "generic": GenericHandler,
}


def get_handler(broker: dict, config: dict, page):
    platform = broker.get("platform", "generic")
    cls = _PLATFORM_MAP.get(platform, GenericHandler)
    return cls(broker, config, page)
