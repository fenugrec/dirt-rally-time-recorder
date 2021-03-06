import asyncore
import os.path
import sys

# Cf. https://stackoverflow.com/a/45488820
try:
    from . import log, config  # @UnusedImport
    from .receiver import Receiver  # @UnusedImport
except (ImportError, ModuleNotFoundError):
    from timerecorder import log, config # @Reimport
    from timerecorder.receiver import Receiver  # @Reimport

logfile = 'timerecord.log'
gitHubOrg = 'https://github.com/soong-construction/'
name = 'dirt-rally-time-recorder'

def informUser():
    input('Press ENTER to end program.')

def main(logfile):
    logger = log.getLogger('timerecorder.timerecord')
    try:
        isBundled = getattr(sys, 'frozen', None)
        if isBundled:
            approot = os.path.dirname(sys.executable)
        else:
            approot = os.path.dirname(os.path.realpath(__file__))
            approot = os.path.dirname(approot) # Move to root
        
        log.init(approot + '/' + logfile)
        logger.info('Starting %s %s', name, config.readVersion(approot))
        
        config.init(approot + '/config.yml')
        
        receiver = Receiver(approot)
        receiver.reconnect()
        
        asyncore.loop()
        
    except KeyboardInterrupt:
        pass
    except:
        logger.exception('***timerecord crashed***')
        logger.error('This should not happen. Look for help at %s%s', gitHubOrg, name)
        informUser()

if __name__ == '__main__':
    main(logfile)
