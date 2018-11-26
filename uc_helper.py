# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ------------------------------------------------------------------------------

r""" Main File for Running Pylint on given Python files and send that output format
    over email. File that performs all database operations like fetching all files
    from a given updateform, Validate the folders and
    python files and access the FormId, BuildId and MountPath through command line

    This file handles the initialization of UCHelper, including:

        a. Initializing file_list list to get output from database queries

        b. Initializing formid_no to access formid argument from command line

        C. Initializing buildid_no to access buildid argument from command line

        d. Initializing mountpath to access mountpath from command line

        e. Initializing dictionary to store file path, email sender, receiver, server, bcc
            to send email

        f. Initializing receiver object to store no. of email receivers from given form

        g. Initializing logger object for logger messages

        h. ...etc...

UCHelper is the only class defined in this file, which handles the operations

UCHelper:

    __init__()                  --  Initialize instance of the UCHelper class,
                                    and the class attributes

    initialize_logger()         --  Initialize the logger object

    read_args()                 --  Reads the arguments from command line as
                                    formid, buildid and mountpath

    query_uc_db(self, query)    --  Adds the logic to connect to UC db and return query output

    get_files_list()            --  Get all the files from given update forms by establishing
                                    database connection

    validate_files()            --  Validate the path of files and python files

    email_receiver()            --  Get Developer, Additional developers and Code reviewers email id
                                    from given update form to send email

    get_receivers_email_alias() --  Get complete email alias of users

    generate_json()             --  Generate dictionary of inputs files to run pylint on it.

    send_notification_email()   --  Send email if execute method gets failed

    execute()                   --  Main method which contains all the methods inside.
                                    Starts the UCHelper execution and also create object
                                    of CVEmailPylint class.

    Usage:

    We can run the file by passing command line arguments as below. for ex.:
    >>PylintBatch.bat -formid 50888 -buildid 1100080 -mountpath F:\PC\test-mount

    Available Command Line arguments:
    formid    --  Update Form ID for which the pylint score is to be determined.

    buildid   -- Build Id reference for which the form is being build.

    mountpath -- Path on the build machine where the source files specified in the form are mounted.

    """

import smtplib
import argparse
import sys
import os
import os.path
import traceback
from email.mime.text import MIMEText
from logger import Logger
import pyodbc
from cvemail_pylint import CvemailPylint


class UCHelper:
    """ Main file to load all the python files in an update form and pass the list
     to Pylint module to perform further operations."""

    def __init__(self):
        """ Initialize instances of the UCHelper class"""
        self.file_list = []
        self.formid_no = None
        self.buildid_no = None
        self.mount_path = None
        self.json_data = {}
        self.receiver = []
        self.logger = None

    def read_args(self):
        """ Reads the arguments from command line as formid, buildid and mountpath.
            Available Command Line Arguments:
            formid    -- Update Form ID for which the pylint score is to be determined.

            buildid   -- Build Id reference for which the form is being build.

            mountpath -- Path on the build machine where the source files specified
                         in the form are mounted.
        """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('-formid', help='Form id  to be processed', dest='Formid')
            parser.add_argument('-buildid', help='Build id to be processed', dest='Buildid')
            parser.add_argument('-mountpath', help='Mount path to be processed', dest='Mountpath')
            arguments = parser.parse_args()
            self.formid_no = arguments.Formid
            self.buildid_no = arguments.Buildid
            self.mount_path = arguments.Mountpath
            self.logger = Logger(self.formid_no).get_log()
        except Exception as args_excep:
            self.logger.info("Passed arguments are not correct %s", str(args_excep))
            raise Exception("Passed arguments are not correct {0}".format(args_excep))

    def query_uc_db(self, query):
        """ add logic to connect to Updatecenter db and return query output"""
        conn = None
        try:
            conn = pyodbc.connect("DRIVER={SQL Server};SERVER=UpdateCenter;"
                                  "DATABASE=ProdUpdateCenter;"
                                  "UID=umsuser;PWD=umsuser")
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as db_excep:
            self.logger.error("Failed to Connect to UpdateCenter with error: %s", db_excep)
            raise Exception("Failed to execute query on UpdateCenter with error:{0}"
                            .format(db_excep))
        finally:
            if conn:
                conn.close()

    def get_files_list(self):
        """ Get all the files from given update form by establishing database connection"""
        get_files_list_query = ("select sSourceFileName from MapFormToSourceFiles where "
                                "nBuildID =%s and nFormID =%s" % (self.buildid_no, self.formid_no))
        self.file_list = self.query_uc_db(get_files_list_query)
        self.logger.info("All files list from given update form %s", self.file_list)

    def validate_files(self):
        """ Filters out the python files from the source files list which are
        placed under Automation or cvpysdk directory."""
        valid_files = []
        for file in self.file_list:
            self.logger.info("File in a list %s", file)
            file = file[0]
            if ((file.startswith('vaultcx/Source/tools/Automation/')
                 or file.startswith('vaultcx/Source/tools/cvpysdk/'))
                    and file.endswith('.py')):
                self.logger.info("Given python file exists as--%s", file)
                valid_files.append(os.path.join(self.mount_path, file))
            else:
                self.logger.info("Given file is not python file or wrong directory as--%s", file)
                self.file_list = valid_files

    def email_receiver(self):
        """ Iterates over all the stake holders of the form and determines the users
        list to whom the email is to be sent."""
        # DevOwner, Additional developers and Code Reviewers(Developer Choice)
        get_email_receiver = ("select spropertyvalue from FormProperties where "
                              "nFormID = {0} and nBuildID = {1} and "
                              "(sPropertyName like 'DevOwner%' or"
                              " sPropertyName like 'Developer%' or"
                              " sPropertyName like 'CodeRevDev%')"
                              .format(self.formid_no, self.buildid_no))
        to_list = self.query_uc_db(get_email_receiver)
        # self.receiver = ''
        for email_receiver in to_list:
            self.receiver.append(email_receiver[0])
        self.logger.info("Receivers List: %s", self.receiver)
        # Code Reviewers(System Enforced)
        system_enforced_cr = ("select distinct sReviewerAlias from "
                              "MapRestrictedRulesToFormCodeReviewers where "
                              "nFormID =%s and nBuildID = %s" % (self.formid_no, self.buildid_no))
        crs_list = self.query_uc_db(system_enforced_cr)
        for crs in crs_list:
            self.receiver.append(crs[0])
        self.logger.info("System Enforced Code Reviewer's List:%s", self.receiver)
        # Developer
        dev_email = ("select sCreatedBy from forminfo where nFormID = %s and nBuildID = %s"
                     % (self.formid_no, self.buildid_no))
        dev_list = self.query_uc_db(dev_email)
        self.receiver.append(dev_list[0][0])
        self.logger.info("Developer's Name:%s", self.receiver)

    def email_receivers_alias(self):
        """ Determine the full alias of email id's of all the users to whom the
        email is to be sent."""
        email_conn = None
        try:
            email_conn = pyodbc.connect(r"DRIVER={SQL Server};SERVER=ENGWEBAGL\ENGWEBDB;"
                                        r"DATABASE=Resources;"
                                        r"UID=readonly;PWD=readonly")
            cursor_dev = email_conn.cursor()
            new_receivers_list = ''
            for single in self.receiver:
                cursor_dev.execute("SELECT emailAlias FROM vwUsers WHERE isDeleted = 0 and "
                                   "ProdcertName In (?);", single)
                developer = cursor_dev.fetchall()
                for dev in developer:
                    new_receivers_list += (dev[0] + "@commvault.com,")
            self.receiver = new_receivers_list
            self.logger.info("All receivers:%s", self.receiver)
        except Exception as alias_excep:
            self.logger.error(r"Failed to connect to ENGWEBAGL\ENGWEBDB with error: %s",
                              alias_excep)
            raise Exception(r"Failed to connect to ENGWEBAGL\ENGWEBDB with error: {0}"
                            .format(alias_excep))
        finally:
            if email_conn:
                email_conn.close()

    def generate_json(self):
        """ Generates dictionary containing files list in update form and email content"""
        self.json_data = {
            "path": self.file_list,
            "Email": {
                "Server": "mail.commvault.com",
                "From": "automation@commvault.com",
                "To":  self.receiver,  #"kdawkhar.cv@commvault.com",
                "Bcc": "kdawkhar.cv@commvault.com",
                }
        }

    @classmethod
    def send_notification_email(cls, mail_exception):
        """ Method to send email notification if code fails.
            Args:
                mail_exception(str) -- Exception to be send over email.
            Returns:
                string - String output exception to be send over email
        """
        body = MIMEText(str(mail_exception), 'plain')
        body['Subject'] = "CVEmailPylint Error Notification"
        body['From'] = "automation@commvault.com"
        body['To'] = ("kdawkhar.cv@commvault.com,jgoel@commvault.com,"
                      "spakhare@commvault.com,kloganathan@commvault.com,") #"kdawkhar.cv@commvault.com"
        server = smtplib.SMTP("mail.commvault.com")
        server.send_message(body)

    def execute(self):
        """ Main method which contains all the methods inside. Starts the UCHelper execution
        and also create object of CvemailPylint class """
        try:
            self.read_args()
            self.get_files_list()
            self.validate_files()
            if self.file_list:
                self.email_receiver()
                # self.conn.close()
                self.email_receivers_alias()
                self.generate_json()
                if self.json_data:
                    obj = CvemailPylint(self.formid_no)
                    obj.json_data = self.json_data
                    obj.execute()
        except Exception as execute_excep:
            self.logger.info("Failed to run execute method as %s", str(execute_excep))
            trace_back = traceback.format_exc()
            self.send_notification_email(trace_back)


if __name__ == "__main__":
    # If no arguments are passed print help message
    if len(sys.argv) <= 1:
        sys.argv.append('-h')

    # Create UCHelper object
    UCH = UCHelper()
    UCH.execute()
