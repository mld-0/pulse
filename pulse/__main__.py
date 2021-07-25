import logging
from .pulse import PulseApp

__version__ = "0.2.0"
_log = logging.getLogger('pulse')

if __name__ == '__main__':
    _log.debug('__main__')
    app = PulseApp()
    app.run()


