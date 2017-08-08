import subprocess
from subprocess import Popen, PIPE

__all__ = (
    'get_subprocess_output',
    'get_latest_pyenv_python_version',
    'print_cmd',
    'print_cmd_step',
    'print_cmd_step_detail',
)


def get_subprocess_output(cmd):
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = p.communicate()
    return out.decode('utf-8')


def get_latest_pyenv_python_version():
    # pyenv install last version
    p = Popen(['pyenv', 'install', '--list'], stdout=PIPE)
    out, err = p.communicate()
    out = out.decode('utf-8')
    version_list = out.split('\n')
    version_list = [x.strip() for x in version_list if x.strip().startswith('3') and 'dev' not in x]
    last_version = version_list.pop()
    return last_version


def print_cmd(value):
    print('== DjangoSetting - %s ==' % value)


def print_cmd_step(value):
    print('- %s' % value)


def print_cmd_step_detail(value):
    print(' %s' % value)
