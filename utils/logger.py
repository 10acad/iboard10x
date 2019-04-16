import logging
import logging.handlers
import os

cdir = os.path.dirname(__file__)

def get_logger(f='code'):
    logger = logging.getLogger(f)
    logger.setLevel(logging.DEBUG)
    #handler = logging.handlers.SysLogHandler(address = '/dev/log')
    handler = logging.FileHandler(os.path.join(cdir,'logging.log'))
    #handler = logging.FileHandler('{0}myLog_{1}-{2}-{3}.log'.format(myLogFileLocation, datem.year, datem.month, datem.day))
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# logging.basicConfig(filename='logging.log',
#                             filemode='a',
#                             format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
#                             datefmt='%H:%M:%S',
#                             level=logging.DEBUG)

