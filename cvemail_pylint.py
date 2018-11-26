# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ------------------------------------------------------------------------------


r""" File for Running Pylint on given Python files, check the file existence, store
    that pylint output in text file and send that email in html format and send Errors
     output format over mail.

    This file handles the initialization of CvemailPylint, including:

        a. initializing json_data dictionary to accept

        b. initializing msg variable to send Email

        c. initializing logger objects for logger messages

        d. initializing footer variable to set the footer of email

        e. initializing form_id variable to set formid

        f. ...etc...

CvemailPylint is the only class defined in this file, which handles the given operations for
the given input json. It operates as a producer/consumer Queue where threads are started and
waiting for items to enter the queue.

CvemailPylint:

    __init__()          -- initialize instance of the CvemailPylint class, and the class attributes.

    initialize_logger() -- Initialize the logger object.

    run_pylint()        -- Runs the pylint on given python file and store it in variable.

    pylint_text()       -- Creates text file and stores the pylint output in it.

    store_pylint()      -- Stores pylint output in a variable in html format

    mail_pylint()       -- Sends html format pylint output through email

    execute()           -- Main method which contains all the methods inside.
                           Starts the CvemailPylint execution.
    """

from email.mime.text import MIMEText
from collections import deque
import sys
import os
import os.path
import subprocess
import smtplib
import re
from constants import PATH
from constants import PYLINT_EXT
from logger import Logger


class CvemailPylint:
    """ Main controller class for running Pylint over given python files"""

    def __init__(self, formid=None):
        """ Initialize instances of the CvemailPylint class"""
        self.json_data = {}
        self.logger = Logger(formid).get_log()
        # self.logger.initialize_logger()
        self.msg = ("<html>"
                    "<body>"
                    "<style> "
                    "#tbl{ width:20%; border: 2px solid black;"
                    "padding: 8px; font-size:15px; font-family: Georgia;}"
                    "#td1{background-color: #b3c6ff; font-family: Georgia;}"
                    "#td2{border: 1px solid #b3c6ff; font-family: Georgia;}"
                    "</style>"
                    "<p style="'font-size:20px; font-family: Georgia;'">"
                    "Hi,<br>  The output of running "
                    "pylint over the list of files shared is:</p></body>"
                    "</html>")
        self.form_id = formid

    def run_pylint(self):
        """ It runs the pylint on given python file and stores it in a list"""
        std_output = []
        try:
            for path in self.json_data["path"]:
                process = subprocess.run(['pylint', path, '-r', 'y'], stdout=subprocess.PIPE)
                std_output.append(process.stdout.decode())
                self.logger.info("Pylint output created for file: %s", path)
        except OSError as fail_pylint:
            self.logger.error("Failed to create pylint output.\n %s", str(fail_pylint))
            raise Exception(str(fail_pylint))

        pylint_output = deque(std_output)
        self.pylint_text(pylint_output)

    def pylint_text(self, pylint_output):
        """ Creates text file within given formid folder name,
            check if folder is exist then store the text file in it and if
            it's not exist then creates the folder with formid and storing
            text file by writing the pylint output in it."""
        try:
            directory = PATH + "\\" + self.form_id
            if os.path.exists(directory):
                for path in self.json_data["path"]:
                    save_path = PATH + "\\" + self.form_id
                    file_name = os.path.splitext(os.path.basename(path))[0]
                    combine_path = file_name + PYLINT_EXT
                    pylint_file = os.path.join(save_path, combine_path)
                    with open(pylint_file, "w") as text_file:
                        self.logger.info("Text file created successfully")
                        text_file.write(str(pylint_output.popleft()))
                        self.logger.info("Wrote Pylint output in text file as %s", pylint_file)
                        text_file.close()
                        self.store_pylint(pylint_file, path)
            else:
                os.makedirs(directory)
                self.logger.info("Directory created as %s", directory)
                for path in self.json_data["path"]:
                    save_path = PATH + "\\" + self.form_id
                    file_name = os.path.splitext(os.path.basename(path))[0]
                    combine_path = file_name + PYLINT_EXT
                    pylint_file = os.path.join(save_path, combine_path)
                    with open(pylint_file, "w") as text_file:
                        self.logger.info("Text file created successfully")
                        text_file.write(str(pylint_output.popleft()))
                        self.logger.info("Wrote Pylint output in text file as %s", pylint_file)
                        text_file.close()
                        self.store_pylint(pylint_file, path)

            self.msg += ("<body><html><h4 style='font-family: Georgia;'>Thanks,<br>"
                         "Commvault Automation Team</h4></body></html>")

        except FileExistsError as file_excep:
            raise Exception("Failed to create pylint output file with error: " + str(file_excep))

    def store_pylint(self, pylint_file, path):
        """ Determines the pylint score from the output and generates the html message out of it."""
        with open(pylint_file) as subfile:
            file = subfile.read()
            pylint_score = re.search(r'(.*)Your code has been rated at (.*)\(previous run:(.*)',
                                     file, re.DOTALL)
            convention_object = re.search(r'(.*)convention \|(.*?)\|(.*)', file, re.DOTALL)
            refactor_object = re.search(r'(.*)refactor   \|(.*?)\|(.*)', file, re.DOTALL)
            warning_object = re.search(r'(.*)warning    \|(.*?)\|(.*)', file, re.DOTALL)
            error_object = re.search(r'(.*)error      \|(.*?)\|(.*)', file, re.DOTALL)
            errors_list_object = re.findall(r'(.*)E:(.*?)\)(.*)', file)
            basefile_name = os.path.basename(pylint_file)
            path_to_textfile = (PATH + "\\{0}\\{1}"
                                .format(self.form_id, basefile_name))

            self.msg += ("<!DOCTYPE html><body><h4 style='font-family: Georgia;'>"
                         "<ul><li style='font-family:Georgia;color:#b30000;'>"
                         + path + "</li></ul><table id= 'tbl'>")

            # Check python file existence
            if not os.path.exists(path):
                self.msg += "<h4>Given python file does not exist</h4>"
            else:
                if pylint_score is not None:
                    if '6' <= pylint_score.group(2) < '8':
                        self.msg += ("<tr><td id='td1'>Pylint Score</td><td id='td2' "
                                     "style='background-color:#ff944d;'>" +
                                     str(pylint_score.group(2))+"</td></tr>")
                    elif pylint_score.group(2) < '6':
                        self.msg += ("<tr><td id='td1'>Pylint Score</td><td id='td2' "
                                     "style='background-color:#ff6666;'>" +
                                     str(pylint_score.group(2))+"</td></tr>")
                    else:
                        self.msg += ("<tr><td id='td1'>Pylint Score</td><td id='td2'>" +
                                     str(pylint_score.group(2)) + "</td></tr>")

                if convention_object is not None:
                    self.msg += ("<tr><td id='td1'>Convention</td><td id='td2'>" +
                                 str(convention_object.group(2).rstrip())+"</td></tr>")

                if refactor_object is not None:
                    self.msg += ("<tr><td id='td1'>Refactor</td><td id='td2'>" +
                                 str(refactor_object.group(2).rstrip())+"</td></tr>")

                if warning_object is not None:
                    self.msg += ("<tr><td id='td1'>Warning</td><td id='td2'>" +
                                 str(warning_object.group(2).rstrip())+"</td></tr>")

                if error_object is not None:
                    if error_object.group(2).rstrip() > '0':
                        self.msg += ("<tr><td id='td1'>Error</td><td id='td2'"
                                     "style='background-color:#ff6666;'>" +
                                     str(error_object.group(2)) + "</td></tr></table>")
                    else:
                        self.msg += ("<tr><td id='td1'>Error</td><td id='td2' "
                                     "style='background-color:#5cd65c;'>" +
                                     str(error_object.group(2)) + "</td></tr></table>")

                if errors_list_object:
                    self.msg += "<h4>Errors:</h4>"
                    for element in errors_list_object:
                        if element[1] is not None:
                            self.msg += "<h4>E:" + str(element[1])+")</h4><br>"
                        else:
                            self.msg += "<h4>Errors:None</h4>"

            self.msg += ("<h4><a href=\"" + path_to_textfile + "\">"
                         + path_to_textfile + "</a></h4><br></body></html>")

    def mail_pylint(self):
        """ Sends email through given server with subject,From,To,Bcc and
            body part containing msg and footer variable content in html format"""
        try:
            body = MIMEText(self.msg, "html")
            body['Subject'] = 'Pylint Score'
            body['From'] = self.json_data["Email"]["From"]
            body['To'] = self.json_data["Email"]["To"]
            body['Bcc'] = self.json_data["Email"]["Bcc"]
            sms = self.json_data["Email"]["Server"]
            sim = smtplib.SMTP(sms)
            sim.send_message(body)
            self.logger.info("Email sent successfully")
        except Exception:
            self.logger.error("Failed to send an email")
            raise Exception("Failed to send an email")

    def execute(self):
        """ Method which contains all the methods inside.
            Starts the CvemailPylint execution."""
        self.run_pylint()
        self.mail_pylint()


if __name__ == "__main__":
    # If no arguments are passed print help message
    if len(sys.argv) <= 1:
        sys.argv.append('-h')

    # Create CVEmailPylint object
    # CVEMAIL = CvemailPylint()
    # CVEMAIL.execute()
