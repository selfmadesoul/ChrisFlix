#!/usr/bin/env python3

import re
import csv
import os
import glob
import logging
from CFLib import *

DEBUG=False

CFLogFile = "/opt/media/tmp/CFLog"
logging.basicConfig(level=logging.DEBUG, filename=CFLogFile, format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

grownMovieFolders = (
    "/opt/media/media2/Grown Up Movies 4",
    "/opt/media/media3/Grown-Up Movies",
    "/opt/media/media5/Grownup Movies2",
    "/opt/media/media6/Grown-Up Movies6",
    "/opt/media/media7/Grown-Up Movies7",
    "/opt/media/media8/Grown-Up Movies8")

grownTVShowFolders = (
    "/opt/media/media2/Grown Up TV4",
    "/opt/media/media3/Grownup TV",
    "/opt/media/media5/Grownup TV2",
    "/opt/media/media6/Grown-Up TV6",
    "/opt/media/media7/Grown-Up TV7",
    "/opt/media/media8/Grown-Up TV8")

kidsMovieFolders = (
    "/opt/media/media2/Kids Movies4",
    "/opt/media/media4/Kids Videos",
    "/opt/media/media6/Kids Movies6",
    "/opt/media/media7/Kids Movies7",
    "/opt/media/media8/Kids Movies8")

kidsTVShowFolders = (
    "/opt/media/media2/Kids TV4",
    "/opt/media/media4/Kids Shows",
    "/opt/media/media6/Kids TV6",
    "/opt/media/media7/Kids TV7",
    "/opt/media/media8/Kids TV8")

def auditMovieFolders(folderTuple, library):

    origFolder = os.getcwd()
    goodRegex = re.compile("^(.*)\s\((\d\d\d\d)\)$")
    movieDict = {}

    for folder in folderTuple:
        if os.path.isdir(folder):
            os.chdir(folder)
            folderList = glob.glob("*")
            for movieFolder in folderList:
                m = goodRegex.search(movieFolder)
                if m:
                    title=m.group(1)
                    year = m.group(2)
                    intYear = int(year)
                else:
                    logger.error("error scanning {}".format(movieFolder))
                    title="error: {}".format(movieFolder)
                    intYear = 9999
                filePath = movieFolder + "/*"
                fileList = glob.glob(filePath)
                for file in fileList:
                    if identifyMovieFile(file):
                        rawSize = os.path.getsize(file)
                        size = round(rawSize / (1024 * 1024 * 1024), 3)

                fullPath = os.path.abspath(movieFolder)
                splitPath = os.path.split(fullPath)
                if os.path.isdir(splitPath[0]):
                    libPath = splitPath[0]
                else:
                    logger.error("{} is not a valid path".format(fullPath))
                    libPath = "invalid: " + fullPath
                movieDict[movieFolder] = (intYear, library, libPath, size)
        else:
            logger.warning("{} is not a valid folder".format(folder))


    os.chdir(origFolder)
    return movieDict

def auditTVShowFolders(folderTuple, Library):

    origFolder = os.getcwd()
    TVDict = {}

    for folder in folderTuple:
        if os.path.isdir(folder):
            os.chdir(folder)
            folderlist = glob.glob("*")
            for tvfolder in folderlist:
                os.chdir(tvfolder)
                seasonList = glob.glob("*")
                seasonCount = 0
                episodeCount = 0
                for season in seasonList:
                    if os.path.isdir(season) and season != "Specials" and season != "Season 00":
                        seasonCount += 1
                        os.chdir(season)
                        episodeList = glob.glob("*")
                        for episode in episodeList:
                            if identifyMovieFile(episode):
                                episodeCount += 1
                        os.chdir("..")
                os.chdir("..")
                fullPath = os.path.abspath(tvfolder)
                splitPath = os.path.split(fullPath)
                if os.path.isdir(splitPath[0]):
                    libPath = splitPath[0]
                else:
                    logger.error("{} is not a valid path".format(fullPath))
                    libPath = "invalid: " + fullPath
                TVDict[tvfolder] = (Library, libPath, seasonCount, episodeCount)
        else:
            logger.warning("{} is not a valid folder".format(folder))

    os.chdir(origFolder)
    return TVDict

if __name__ == "__main__":

    grownMovieDict = auditMovieFolders(grownMovieFolders, "Grown-Up Movies")
    allMovieDict = auditMovieFolders(kidsMovieFolders, "Kids Movies")

    allMovieDict.update(grownMovieDict)


    fieldNames = ("Title", "Year", "Library", "Library Path", "Size")
    movieCSVPath = "/opt/media/tmp/movies.csv"
    with open(movieCSVPath, 'w', newline='') as movieCSVfile:
        movieWriter = csv.writer(movieCSVfile)
        movieWriter.writerow(fieldNames)
        linesWriten = 0
        for title in allMovieDict.keys():
            row = ()
            rows = []
            dataList = allMovieDict[title]
            if len(dataList) >= 4:
                year, library, libPath, size = dataList
            else:
                logger.error("Malformed Movie: {} with dataset {}".format(title, dataList))
            year, library, libPath, size = allMovieDict[title]
            row = (title, year, library, libPath, size)
            if DEBUG:
                logger.info("Writing movie {}".format(row))
            movieWriter.writerow(row)
            linesWriten += 1
        logging.info("Wrote {} movies".format(linesWriten))

    grownTVDict = auditTVShowFolders(grownTVShowFolders, "Grown-Up TV")
    allTVDict = auditTVShowFolders(kidsTVShowFolders, "Kids TV")

    allTVDict.update(grownTVDict)

    fieldNames = ("Title", "Library", "Library Path", "Seasons", "Episodes")
    tvCSVPath = "/opt/media/tmp/tvseries.csv"
    with open(tvCSVPath, 'w', newline='') as tvCSVfile:
        tvWriter = csv.writer(tvCSVfile)
        tvWriter.writerow(fieldNames)
        linesWriten = 0
        for title in allTVDict.keys():
            row = ()
            rows = []
            dataList = allTVDict[title]
            if len(dataList) >= 4:
                library, libPath, seasons, episodes = dataList
            else:
                logging.error("Malformed TV Show: {} with dataset {}".format(title, dataList))
            row = (title, library, libPath, seasons, episodes)
            if DEBUG:
                logger.info("Writing show {}".format(row))
            tvWriter.writerow(row)
            linesWriten += 1
        logging.info("Scanned {} shows".format(linesWriten))

    emailFileNames = [movieCSVPath, tvCSVPath]
    CFMailFile(emailFileNames, "Movie and TV CSVs", "csv")
