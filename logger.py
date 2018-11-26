# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ------------------------------------------------------------------------------
"""" Main file initializes logger of CVEmailPylint package.

This module handles the initialization of logger object for the log files.
Logger:
        __init__(self,formid)             -- Initializes logger of Logger class

        __initialize_logger(self, formid) -- Initializes the logger for CVemailPylint package

        get_log()                          -- Returns the log object for current thread
                                             if exists else create a new standalone logger
                                             for current thread
"""

import logging
import os
from constants import PATH
from constants import LOGCONSTANT


class Logger:
    """"Logger class for CVEmailPylint package."""

    def __init__(self, formid):
        self.__initialize_logger(formid)

    def __initialize_logger(self, formid):
        """ Initialize the logger for the CvemailPylint run"""
        try:
            logger = logging.getLogger()
            logger.setLevel(logging.INFO)
            logpath = os.path.join(PATH, formid, LOGCONSTANT)
            # Create File handler
            handler = logging.FileHandler(logpath)
            handler.setLevel(logging.INFO)

            # Create logging format
            formatter = logging.Formatter('%(process)-6d  %(thread)-6d  %(asctime)-25s'
                                          '  %(module)-16s  %(funcName)-25s'
                                          ' %(lineno)-6d  %(levelname)-15s %(message)s')
            handler.setFormatter(formatter)

            # add handlers to logger
            logger.addHandler(handler)
            logger.info("*" * 80)
            logger.info("%(boundary)s  %(message)s %(boundary)s",
                        {'boundary': "*" * 25,
                         'message': "CVEmail Execution Started"
                        })
            logger.info("*" * 80)
        except Exception as excp:
            raise Exception("Failed to initialize logger with error: {0}".format(excp))

    def get_log(self):
        return logging.getLogger()

