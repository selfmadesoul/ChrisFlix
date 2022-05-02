#!/usr/bin/env python3

#This is a collection of subroutines used across other ChrisFlix scripts

import sys
import os
import glob
import re
import mimetypes
import logging
import smtplib
import subprocess
from email.message import *


DEBUG=False

CFLogFile = "/opt/media/tmp/CFLog"
logging.basicConfig(level=logging.DEBUG, filename=CFLogFile, format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

def identifyMovieFile(filename):
    #Bug in Python 3.7.3+ that requires a MimeType to be added for m4vs
    mimetypes.add_type('video/x-m4v', '.m4v')
    minimumFileSize = 30000000

    if os.path.isfile(filename) == False:
        #Don't even bother to test anything else if it isn't even a file
        return False

    mimeTuple = mimetypes.guess_type(filename)
    mimeInfo = mimeTuple[0]

    isMediaFile = False
    isLargeEnough = False
    mimeTypeMatch = False

    for element in filename.split("."):
        if "MP4" in element.upper():
            isMediaFile = True
        elif "MKV" in element.upper():
            isMediaFile = True
        elif "AVI" in element.upper():
            isMediaFile = True
        elif "M4V" in element.upper():
            isMediaFile = True

    if os.path.isfile(filename) and os.path.getsize(filename) >= minimumFileSize:
        isLargeEnough = True

    if mimeInfo:
        if "VIDEO" in mimeInfo.upper():
            mimeTypeMatch = True

    if DEBUG:
        logger.debug("isMediaFile, isLargeEnough, mimeTypeMatch are {} {} and {}".format(isMediaFile, isLargeEnough, mimeTypeMatch))

    if isMediaFile and isLargeEnough and mimeTypeMatch:
        return True
    else:
        return False


def createMovieFolder(filename):
    #We found a movie file without a folder and we are now creating one
    fileRegex = re.compile("^(.+)(\d{4})[^p].+$")
    total = fileRegex.search(filename)

    try:
        rawTitle = total.group(1)
        year = int(total.group(2))
        title = rawTitle.replace(".", " ")
    except:
        logger.error("Cannot create Movie Folder for {}".format(filename))
        return False
    newFolder = title + str(year) + ")"
    os.mkdir(newFolder, 0o775)
    os.chdir(newFolder)

    oldFilePath = "../" + filename

    if "." in filename:
            for element in filename.split("."):
                if "MKV" in element.upper():
                    fileType = ".mkv"
                elif "AVI" in element.upper():
                    fileType = ".avi"
                elif "M4V" in element.upper():
                    fileType = ".m4v"
                else:
                    fileType = ".mp4"


    newFileName = newFolder + fileType
    os.rename(oldFilePath, newFileName)
    logger.info("Changing {} to {}".format(oldFilePath, newFileName))

    os.chdir("..")


def fixMovieFolder(origFolder):
    badRegex = re.compile("^([A-Za-z0-9\.]+).+(\d\d\d\d).+(\d{3,4}p).*$")
    total = badRegex.search(origFolder)

    if (total):
        rawTitle = total.group(1)
        year = int(total.group(2))
        title = rawTitle.replace(".", " ")
    else:
        logger.error("Error fixing folder {}".format(origFolder))
        return 1

    newFolder = title + " (" + str(year) + ")"

    if origFolder == newFolder:
        return(1)
    elif os.path.isdir(newFolder) == False:
        logger.info("Renaming folder {} to {}".format(origFolder, newFolder))
        if os.path.isdir(origFolder):
            os.rename(origFolder, newFolder)
        else:
            logger.error("Can't find folder {} to rename".format(origFolder))
        os.chdir(newFolder)

        filelist = glob.glob("*")


        for item in filelist:
            if item == "Subs" and os.path.isdir("Subs"):
                logger.info("Leaving Subs alone!")
                #Subtitle folder. Move along please
            elif identifyMovieFile(item):
                #This is the actual movie file most likely
                videotype = item.split(".")[-1]
                newFileName = newFolder + "." + videotype

                if os.path.isfile(newFileName) == False:
                    logger.info("Renaming file {} to {}".format(item, newFileName))
                    os.rename(item, newFileName)
            else:
                #Nothing Else Matters
                logger.info("Deleting {}".format(item))
                os.remove(item)

        os.chdir("..")

def CFMailFile(filenames,subject,type):
    msg=EmailMessage()
    msg['Subject']=subject
    msg['From']="chris@terrysrv"
    msg["To"]="christerryatl@gmail.com"
    if type == "csv":
        filemaintype="text"
        filesubtype="csv"
    for file in filenames:
        with open(file,'rb') as fp:
            paths=os.path.split(file)
            data=fp.read()
            msg.add_attachment(data, maintype=filemaintype, subtype=filesubtype, filename=paths[1])
    with smtplib.SMTP('localhost') as s:
        s.send_message(msg)
    return True

def checkTransmissionComplete(torrent):
    output = []
    if DEBUG:
        logger.info("Checking on completion status of {}".format(torrent))
    transmissionPath="/usr/bin/transmission-remote"
    output = subprocess.run([transmissionPath, "-l"], stdout=subprocess.PIPE).stdout.decode('utf-8')
    outputLines = output.split("\n")
    for line in outputLines:
        if DEBUG:
            logger.info(line)
        if torrent in line:
            if DEBUG:
                logger.info("Found torrent {} in line {}".format(torrent, line))
            [id, completion, haveNum, haveType, eta, upload, download, ratio, status, torrentName] = line.split()
            if (completion == "100%") and (eta == "Done") and (status == "Seeding" or status == "Idle"):
                logger.info("Found valid item {} with status {}".format(torrent, status))
                return True
    logger.info("Did not find a completed Torrent in {} at {}".format(torrent, completion))
    return False

def verifyMovieFolder(folder):
    globPath = folder + "/*"
    if os.path.isdir(folder):
        fileList = glob.glob(globPath)
        for file in fileList:
            if identifyMovieFile(file):
                logger.info("Verified Movie Folder {} with file {}".format(folder, file))
                return True
    else:
        return False
    return False

def yoinkTorrent(torrent):
    if DEBUG:
        logger.info("yoinkTorrent() invoked with torrent {}".format(torrent))
    output = []
    successString = "success"
    if DEBUG:
        logger.info("Checking on completion status of {}".format(torrent))

    #We need to find the ID in transmission for the torrent to remove

    transmissionPath="/usr/bin/transmission-remote"
    output = subprocess.run([transmissionPath, "-l"], stdout=subprocess.PIPE).stdout.decode('utf-8')
    outputLines = output.split("\n")
    for line in outputLines:
        if DEBUG:
            logger.info(line)
        if torrent in line:
            if DEBUG:
                logger.info("Found torrent {} in line {}".format(torrent, line))
            [id, completion, haveNum, haveType, eta, upload, download, ratio, status, torrentName] = line.split()
    if (completion == "100%") and (eta == "Done") and (status == "Seeding" or status == "Idle"):
        logger.info("Removing Torrent {} from Transmission".format(torrent))
        try:
            syntax=transmissionPath + " -t {}".format(id) + " -r"
            logger.info("Using syntax '{}'".format(syntax))
            output = subprocess.run(syntax,stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8')
            logger.info(output)
        except:
            logger.error("Could not execute transmission-remote properly")
            quit()
        if successString in output:
            return True
        else:
            logger.error("Transmission remove command failed with error - {}".format(output))
            return False
