import logging.config
import os

from logging import Logger

from logger.ColorFormatter import ColorFormatter
from logger.FileFormatter import FileFormatter


class LoggerLoader:

    def __init__(self, filename: str, level: str, log_dir: str = '/var/log/'):
        self._logger_name = 'Main'
        self._level = level

        self._filename = filename
        self._log_directory = log_dir
        self._filepath = f'{self._log_directory}{self._filename}'

        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        logging.ColorFormatter = ColorFormatter
        logging.FileFormatter = FileFormatter

        self._configure_logging()

    def _configure_logging(self):
        logging.config.dictConfig({
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'file': {
                    'level': self._level,
                    'class': 'logging.FileHandler',
                    'filename': self._filepath,
                    'formatter': 'file'
                },
                'console': {
                    'level': self._level,
                    'class': 'logging.StreamHandler',
                    'formatter': 'console'
                }
            },
            'formatters': {
                'file': {
                    'class': 'logging.FileFormatter',
                    'datefmt': '%Y.%m.%d %H:%M:%S'
                },
                'console': {
                    'class': 'logging.ColorFormatter',
                    'datefmt': '%Y.%m.%d %H:%M:%S'
                }
            },
            'loggers': {
                self._logger_name: {
                    'handlers': ['file', 'console'],
                    'level': self._level,
                    'propagate': False
                }
            }
        })

    def change_logger_level(self, level: str):
        if level not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
            raise Exception(f'Unknown Logger Level {level}')

        self._level = level
        self._configure_logging()

    def get_logger(self) -> Logger:
        return logging.getLogger(self._logger_name)
