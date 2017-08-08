import subprocess

__all__ = (
    'Pyenv',
)


class Pyenv:
    def __init__(self, pyenv_path):
        self.pyenv_path = pyenv_path

    def call(self, cmd):
        subprocess.call('%s/bin/%s' % (
            self.pyenv_path,
            cmd
        ), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
