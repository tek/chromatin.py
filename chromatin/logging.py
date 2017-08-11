import amino.logging
import ribosome.logging
from ribosome.logging import ribosome_logger

from amino.lazy import lazy


log = chromatin_root_logger = ribosome_logger('chromatin')


def chromatin_logger(name: str):
    return chromatin_root_logger.getChild(name)


class Logging(ribosome.logging.Logging):

    @lazy
    def _log(self) -> amino.logging.Logger:
        return chromatin_logger(self.__class__.__name__)

__all__ = ('chromatin_logger', 'Logging')
