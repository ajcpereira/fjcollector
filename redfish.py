

from functions.server import *

logging.basicConfig(filename='logs/power.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(module)s %(threadName)s %(message)s', force=True)

server_power()
