import logging
import sys
from .pulse import PulseApp

_log = logging.getLogger('pulse')
_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(level=logging.DEBUG, format=_logging_format, datefmt=_logging_datetime, stream=sys.stderr)

__version__ = "0.2.0"
#_log = logging.getLogger('pulse')

if __name__ == '__main__':
    _log.debug('__main__')
    app = PulseApp()
    app.run()


