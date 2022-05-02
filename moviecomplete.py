#!/usr/bin/env python3

#This program scans the folder of completed movies in the Bitorrent client,
# verifies that the client has finished downloading it, and places it in the
# appropriate folder.

import os
import glob
import logging
import sys
import re
import shutil
import socket
from CFLib import *

DEBUG = False

CFLogFile = "/opt/media/tmp/CFLog"
logging.basicConfig(level=logging.DEBUG, filename=CFLogFile, format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

def handleError(func, path, exc_info):
    logger.error('Handling Error for file ' , path)
    logger.error(exc_info)

if __name__ == "__main__":

    hostname = "seedbox"
    if socket.gethostname() != hostname:
        logger.error("Incorrect hostname {}. This MUST be run from 'seedbox'".format(socket.gethostname()))


    downloadPath = "/opt/media/transmission/incomplete/"
    downloadGlob = downloadPath + "*"
    if  sys.argv[1]:
        destPath = sys.argv[1] + "/"
    else:
        logger.error("Requires an argument: Destination directory for movie folder")
        quit()

    if os.path.isdir(downloadPath):
        folderList = glob.glob(downloadGlob)
    else:
        logger.error("Can't open download folder {}".format(downloadPath))
        quit()

    for folder in folderList:
        if DEBUG:
            logger.info("Evaluating {}".format(folder))
        if os.path.isdir(folder):
            if DEBUG:
                logger.info("Found {}, moving there".format(folder))
            os.chdir(folder)
        else:
            logger.error("Cannot change to folder {}".format(folder))
        fileList = glob.glob("*")
        movieComplete = False
        for file in fileList:
            elements = file.split(".")
            if elements[-1] == "part":
                movieComplete = False
                if DEBUG:
                    logger.info("Found that {} is not complete with {} containing .part".format(folder, file))
                continue
            else:
                if identifyMovieFile(file):
                    if DEBUG:
                        logger.info("Found a movie file in {}".format(file))
                    parts=os.path.split(folder)
                    torrent=parts[-1]
                    if checkTransmissionComplete(torrent):
                        logger.info("Found a completed movie file {} in torrent {}".format(file, folder))
                        movieComplete = True

        os.chdir("..")
        if movieComplete == True:
            src = folder
            torrentName = os.path.split(src)[-1]
            dst = destPath + torrentName
            if os.path.isdir(dst):
                if DEBUG:
                    logger.info("Folder {} is already in place at {}".format(src, dst))
                    continue
            else:
                logger.info("copying {} to {}".format(src, dst))
                try:
                    shutil.copytree(src, dst)
                except:
                    logger.error("Could not copy {} to {}".format(src, dst))

                #Now lets verify FOR SURE that the  movie is in place before we
                #remove the torrent from the client (yoink it)

                if verifyMovieFolder(dst):
                        logger.info("Verified copy to {}, now going to yoink from Transmission".format(dst))
                        if yoinkTorrent(torrentName):
                            logger.info("Yoink successful. Removing {} from torrent folders".format(torrentName))
                            shutil.rmtree(src, onerror=handleError)
                        else:
                            logger.error("Removal of {} from Transmission was NOT successful".format(torrentName))
                else:
                    logger.error("Could not verify that {} is safely in {}".format(torrent, dst))
