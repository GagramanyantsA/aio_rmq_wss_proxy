from logging import Formatter


class FileFormatter(Formatter):

    def __init__(self, *args, **kwargs):
        # can't do super(...) here because Formatter is an old school class
        Formatter.__init__(self, *args, **kwargs)

    def format(self, record):
        levelname = record.levelname

        if levelname in {'WARNING', 'CRITICAL', 'ERROR'}:
            self._style._fmt = '%(asctime)s %(levelname)-8s %(message)s %(filename)+30s %(lineno)d'
        else:
            self._style._fmt = '%(asctime)s %(levelname)-8s %(message)s'

        message = Formatter.format(self, record)

        return message
