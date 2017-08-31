import json
import os
import re
import shutil
import subprocess
from subprocess import DEVNULL, STDOUT

from .functions import *
from ..utils import *


class StartProject:
    def __init__(self, project_name):
        self.CWD = os.getcwd()
        self.PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.PACKAGE_CODE_DIR = os.path.join(self.PACKAGE_DIR, 'codes')
        self.PACKAGE_FILE_DIR = os.path.join(self.PACKAGE_DIR, 'files')

        # argv check
        self.project_name = project_name
        self.env_name = '%s-env' % self.project_name

        # Project, Django paths
        self.PROJECT_DIR = os.path.join(self.CWD, self.project_name)
        self.DJANGO_DIR = os.path.join(self.PROJECT_DIR, 'django_app')
        self.DJANGO_CONFIG_DIR = os.path.join(self.DJANGO_DIR, 'config')
        self.DJANGO_SETTINGS_DIR = os.path.join(self.DJANGO_CONFIG_DIR, 'settings')

        # pyenv version specify
        self.python_version = select_python_version()

        # pyenv
        self.pyenv_path = None
        self.pyenv = None

        # Secret dict
        self.secret_dict = {}

    def execute(self):
        self.check_requirements()
        self.make_project_dir()
        self.pyenv_process()
        self.project_structure_process()
        self.django_structure_process()
        self.manage_apps()
        self.manage_settings()
        self.manage_config_files()
        self.finishing()

    def check_requirements(self):
        print_cmd_step('Check requirements')
        # pyenv check
        check_pyenv_installed()

    def make_project_dir(self):
        print_cmd_step('Make project directory')
        os.chdir(self.CWD)
        # Make project folder
        if os.path.exists(self.project_name):
            shutil.rmtree(self.project_name)
        # subprocess.call('pyenv uninstall -f %s' % env_name, shell=True)
        os.mkdir(self.project_name)
        os.chdir(self.project_name)

    def pyenv_process(self):
        print_cmd_step('pyenv process')
        os.chdir(self.PROJECT_DIR)
        # pyenv make virtualenv
        subprocess.call('pyenv virtualenv %s %s' % (
            self.python_version,
            self.env_name,
        ), shell=True, stdout=DEVNULL, stderr=STDOUT)

        # pyenv local
        subprocess.call('pyenv local %s' % (
            self.env_name,
        ), shell=True, stdout=DEVNULL, stderr=STDOUT)

        # pyenv path
        self.pyenv_path = get_pyenv_path(self.env_name)
        self.pyenv = Pyenv(self.pyenv_path)

    def project_structure_process(self):
        print_cmd_step('Project structure process')
        os.chdir(self.PROJECT_DIR)
        os.mkdir('.config')
        os.mkdir('.config_secret')
        os.mkdir('.requirements')
        os.mkdir('.media')
        os.mkdir('.static_root')

        # .gitignore file
        open('.gitignore', 'w').write(open(os.path.join(self.PACKAGE_FILE_DIR, 'gitignore')).read())

        # install django, startproject
        self.pyenv.call('pip install django django_extensions ipython')
        self.pyenv.call('django-admin startproject config')
        self.pyenv.call('pip freeze > .requirements/debug.txt')

        # django application folder rename
        os.rename('config', 'django_app')

    def django_structure_process(self):
        print_cmd_step('Django structure process')
        os.chdir(self.DJANGO_DIR)
        os.mkdir('templates')
        os.mkdir('static')

        # Create apps
        self.pyenv.call('python manage.py startapp member')

    def manage_apps(self):
        print_cmd_step('Manage Django applications')
        os.chdir(self.DJANGO_DIR)

        def manage_member():
            open('member/models.py', 'w').write(
                open(os.path.join(self.PACKAGE_CODE_DIR, 'member', 'models')).read())

        manage_member()

    def manage_settings(self):
        print_cmd_step('Manage Django settings')
        # 기존 settings.py파일을 읽고 지움
        os.chdir(self.DJANGO_CONFIG_DIR)
        original_settings = open('settings.py').read()
        os.remove('settings.py')

        # settings패키지를 생성
        os.mkdir('settings')
        open('settings/__init__.py', 'w').write(
            open(os.path.join(self.PACKAGE_CODE_DIR, 'settings', '__init__')).read())

        # settings/base.py파일 생성
        base_settings = self._sub_settings(self._get_secret_values(original_settings))
        open('settings/base.py', 'w').write(base_settings)

        # settings/debug.py파일 생성
        open('settings/debug.py', 'w').write(
            open(os.path.join(self.PACKAGE_CODE_DIR, 'settings', 'debug')).read())

    def manage_config_files(self):
        os.chdir(self.PROJECT_DIR)
        print_cmd_step('Manage Django config files')
        # secret config to json file
        secret_config = {
            'django': {
                'secret_key': self.secret_dict['secret_key'],
            }
        }
        open('.config_secret/settings_common.json', 'w').write(
            json.dumps(secret_config, indent=4, sort_keys=True))

    def finishing(self):
        print_cmd_step('Finishing')
        os.chdir(self.DJANGO_DIR)
        self.pyenv.call('python manage.py makemigrations')
        self.pyenv.call('python manage.py migrate')

        os.chdir(self.PROJECT_DIR)
        subprocess.call('git init', shell=True, stdout=DEVNULL)
        subprocess.call('git add -A', shell=True, stdout=DEVNULL)
        subprocess.call('git commit -m \'First commit\'', shell=True, stdout=DEVNULL)

    def _get_secret_values(self, settings):
        secret_list = [
            {
                'regex': r'SECRET_KEY = \'(?P<secret_key>.*?)\'.*?\n',
                'key': 'secret_key',
                'group': 'secret_key',
                'preserve': False
            }
        ]
        for secret in secret_list:
            value = re.search(secret['regex'], settings).group(secret['group'])
            self.secret_dict[secret['key']] = value
            if value and not secret.get('preserve'):
                settings = re.sub(secret['regex'], '', settings)
        return settings

    def _sub_settings(self, settings):
        import_pattern = r'import os'
        import_repl = r'import os\nimport json'
        project_name_pattern = 'Django settings for config project.'
        project_name_repl = 'Django settings for %s project.' % self.project_name
        paths_pattern = r'\n(BASE_DIR.*?\n)'
        paths_repl = open(os.path.join(self.PACKAGE_CODE_DIR, 'settings', 'base')).read()
        remove_comment_secret_pattern = re.compile(r'(# SECURITY WARNING: keep the secret.*?\n)', re.DOTALL)
        remove_comment_secret_repl = ''
        templates_pattern = re.compile(
            r'(?P<before>\nTEMPLATES = .*?\n)(?P<indent>\s+)(?P<key>\'DIRS\': )(?P<value>\[\]),',
            re.DOTALL
        )
        templates_repl = r'\g<before>\g<indent>\g<key>[\n\g<indent>    TEMPLATE_DIR,\n\g<indent>],'
        installed_apps_pattern = re.compile(r'(\nINSTALLED_APPS = .*?)(\n])', re.DOTALL)
        installed_apps_repl = r'%s' % (
            open(os.path.join(self.PACKAGE_CODE_DIR, 'settings', 'base_installed_apps')).read()
        )

        replacements = {
            # import
            import_pattern: import_repl,
            # project name
            project_name_pattern: project_name_repl,
            # root, template, static paths
            paths_pattern: paths_repl,
            # remove comments
            remove_comment_secret_pattern: remove_comment_secret_repl,
            # template dirs
            templates_pattern: templates_repl,
            # INSTALLED_APPS
            installed_apps_pattern: installed_apps_repl,
        }

        for src, target in replacements.items():
            settings = re.sub(src, target, settings)

        return settings
