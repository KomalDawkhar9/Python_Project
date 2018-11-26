# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ------------------------------------------------------------------------------

r"""File that runs Cleanup Script for folders ie. removes folders from path after every 15 days
    \\devshare\CoreAutomation\\Pylint\\ which are being official"""

import time
import shutil
import os
import pyodbc


class PylintCleanup:
    """Class for running script to clean up folders in devshare which are get official"""
    def __init__(self):
        self.dev = set()
        self.form_state_path = set()
        self.devshare_path = None

    def check_path(self):
        """ Check the folders from devshare."""
        path = r"\\devshare\devl\CoreAutomation\Pylint"
        file = []
        for _, dirnames, filenames in os.walk(path):
            # files = len(filenames)
            # folders = len(dirnames)
            file += dirnames
        self.devshare_path = set(file)
        print("Devshare:", self.devshare_path)

    def check_form_state(self):
        """Checks only official folders from update center database"""
        connection = None
        form_state = []
        try:
            connection = pyodbc.connect("DRIVER={SQL SERVER};SERVER=UpdateCenter;"
                                        "DATABASE=ProdUpdateCenter;"
                                        "UID=umsuser;PWD=umsuser")
            cursor = connection.cursor()
            cursor.execute("select nFormID from forminfo join CVFormState on "
                           "forminfo.nFormStateID = CVFormState.nFormStateID AND "
                           "sDisplayName= 'official'")
            form_state = cursor.fetchall()
            for onestate in range(len(form_state)):
                self.form_state_path.add(str(form_state[onestate][0]))

            print("form state path:", self.form_state_path)
        except Exception as state_excep:
            print("Failed to connect to UpdateCenter with error: %s", state_excep)
            raise Exception("Failed to connect to UpdateCenter with error: {0}".format(state_excep))
        finally:
            if connection:
                connection.close()

    def cleanup_script(self):
        """Checks the official forms from devshare by comparing it with
        forms from updatecenter and delete related directory if present."""
        try:
            final_set = self.devshare_path & self.form_state_path
            print("Common elements:", final_set)
            now = time.time()
            cutoff = now - (1*300)
            for one_element in final_set:
                share_path = r"\\devshare\devl\CoreAutomation\Pylint"
                join_path = share_path + "\\" + one_element
                # print("Join path:", join_path)
                # files = os.listdir(share_path)
                # print("Files:", files)
                if final_set:
                    if os.path.isdir(join_path):
                        time_file = os.stat(join_path)
                        time_folder_creation = time_file.st_ctime
                        if time_folder_creation < cutoff:
                            shutil.rmtree(join_path, ignore_errors=False, onerror=None)
                            print("Directory gets cleaned up as ", one_element)
                        else:
                            print("No directory is official yet")
                else:
                    print("No any Official form folder found here")
        except FileNotFoundError as exception:
            print(exception)

    def execute(self):
        """ Method which contains all the methods inside.
         Starts the pylint_cleanup_script execution."""
        self.check_path()
        self.check_form_state()
        self.cleanup_script()


if __name__ == "__main__":

    PYCLEANUP = PylintCleanup()
    PYCLEANUP.execute()
