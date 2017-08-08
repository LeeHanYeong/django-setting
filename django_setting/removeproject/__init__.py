import os
import shutil
import subprocess
import sys
from distutils.util import strtobool


class RemoveProject:
    def __init__(self, project_name):
        self.CWD = os.getcwd()
        self.PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.PACKAGE_CODE_DIR = os.path.join(self.PACKAGE_DIR, 'codes')
        self.PACKAGE_FILE_DIR = os.path.join(self.PACKAGE_DIR, 'files')

        # argv check
        self.project_name = project_name
        self.env_name = '%s-env' % self.project_name

    def execute(self):
        os.chdir(self.CWD)
        ask = input(
            'Do you want to clear "%s" project folder and "%s" virtual environment? (y/n): ' % (
                self.project_name,
                self.env_name
            ))
        if not strtobool(ask):
            sys.exit()
        shutil.rmtree(self.project_name)
        subprocess.call('pyenv uninstall -f %s' % self.env_name, shell=True)
        print('Remove project %s complete' % self.project_name)
