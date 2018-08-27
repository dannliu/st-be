import os
import dotenv
import logging.config

dotenv.load_dotenv(dotenv.find_dotenv())

logging.getLogger(__name__).addHandler(logging.NullHandler())
logging.basicConfig(level=logging.DEBUG)
basedir = os.path.abspath(os.path.dirname(__file__))
logging.config.fileConfig(os.path.join(basedir, 'logging.cfg'),
                          disable_existing_loggers=False)

