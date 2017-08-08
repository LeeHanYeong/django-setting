import re
import shutil
import sys
from subprocess import Popen, PIPE
from ..utils.common import get_subprocess_output

__all__ = (
    'check_pyenv_installed',
    'select_python_version',
    'get_pyenv_path',
)


def check_pyenv_installed():
    """
    Check pyenv is installed on system

    시스템에 pyenv가 설치되어 있는지 검사합니다
    :return: None, if not installed execute sys.exit()
    """
    if not shutil.which('pyenv'):
        print('pyenv must be installed')
        sys.exit()
    if not shutil.which('pyenv-virtualenv'):
        print('pyenv-virtualenv must be installed')
        sys.exit()


def select_python_version():
    """
    Run the 'pyenv versions' command and parse the results to return a list of versions

    'pyenv versions'명령어를 실행 후 결과를 파싱해 버전 목록을 반환합니다
    :return: pyenv installed python versions
                (ex: [2.7.12, 3.6.1, 3.6.2])
    """
    p = Popen(['pyenv', 'versions'], stdout=PIPE)
    out, err = p.communicate()
    out = re.sub(r' \(set by.*\)', '', out.decode('utf-8').replace('*', ''))
    version_list = [x.strip() for x in out.split('\n') if
                    x.strip().startswith('3') and '/' not in x]
    if len(version_list) == 1:
        return version_list[0]
    select_string = 'Available python versions:\n'
    for index, version in enumerate(version_list):
        select_string += ' %s] %s\n' % (index + 1, version)
    select_string += '  Select python version (default: %s): ' % version_list[len(version_list) - 1]
    selected_version = input(select_string)
    print('')
    if not selected_version:
        selected_version = len(version_list)
    return version_list[int(selected_version) - 1]


def get_pyenv_path(env_name):
    """
    Returns the path to the virtual environment given by 'env_name'
    (Search only in the virtual environment created by pyenv)

    'env_name'으로 주어진 가상환경(pyenv로 생성한 가상환경에서만 검색)의 경로를 반환합니다.
    :param env_name: virtualenv's name
    :return: Path of the virtual environment named 'env_name'
    """

    env_list = get_subprocess_output('pyenv virtualenvs').split('\n')

    def get_version_path(m):
        return '{},{}'.format(m.group(1), m.group(2))

    p = re.compile(r'\s*([\w\W]+?)\s\(created from\s([\w\W]+?)\)')
    env_list = [re.sub(p, get_version_path, env).split(',') for env in env_list if
                env.strip().startswith(env_name)]
    env = env_list[0]
    path = '{}/envs/{}'.format(env[1], env[0])
    return path
