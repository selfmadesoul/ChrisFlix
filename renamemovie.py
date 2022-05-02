#!/usr/bin/env python3

import sys
import os
import glob
import re
import logging
from CFLib import identifyMovieFile, createMovieFolder, fixMovieFolder

DEBUG=False

CFLogFile = "/opt/media/tmp/CFLog"
logging.basicConfig(level=logging.DEBUG, filename=CFLogFile, format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":

    globPath = sys.argv[1] + "/*"

    improperNames = []

    filelist = glob.glob(globPath)
    goodRegex = re.compile("^(.*)\s\((\d\d\d\d)\)$")

    os.chdir(sys.argv[1])

    for item in filelist:
        if DEBUG:
            logger.debug("Evaluating {}".format(item))
        head, tail = os.path.split(item)

        if identifyMovieFile(tail):
            # Is this a bare movie file in a Movie Library?
            createMovieFolder(tail)
            # If so, make a folder for it and move it there
            continue

        elif " " in tail:
            # The presence of whitespace indicates that its a normal folder
            if DEBUG:
                logger.debug("Leaving {} alone".format(tail))
            total  = goodRegex.search(tail)

            #Need to check and make sure the format is normal
            try:
                    title = total.group(1)
                    year = total.group(2)
            except:
                    logger.error("Abnormal format in {}".format(tail))
            continue

        else:
            improperNames.append(item)
            logger.info("Normalizing folder for {}".format(item))
            fixMovieFolder(tail)
