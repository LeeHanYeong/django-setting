import json
import os
import shutil
import subprocess


class SettingsBuild:
    def __init__(self, project_name):
        self.mode = 'debug'

        self.CWD = os.getcwd()
        self.PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.PACKAGE_CODE_DIR = os.path.join(self.PACKAGE_DIR, 'codes')
        self.PACKAGE_FILE_DIR = os.path.join(self.PACKAGE_DIR, 'files')

        # argv check
        self.project_name = project_name
        self.env_name = '%s-env' % self.project_name

        # Project, config paths
        self.PROJECT_DIR = os.path.join(self.CWD, self.project_name)
        self.CONFIG_DIR = os.path.join(self.PROJECT_DIR, '.config')
        self.CONFIG_DOCKER_DIR = os.path.join(self.CONFIG_DIR, 'docker')
        self.CONFIG_NGINX_DIR = os.path.join(self.CONFIG_DIR, 'nginx')
        self.CONFIG_SUPERVISOR_DIR = os.path.join(self.CONFIG_DIR, 'supervisor')
        self.CONFIG_UWSGI_DIR = os.path.join(self.CONFIG_DIR, 'uwsgi')
        self.CONFIG_PUBLIC_FILE = os.path.join(self.CONFIG_DIR, 'settings_public.json')

        self.CONFIG_SECRET_DIR = os.path.join(self.PROJECT_DIR, '.config_secret')
        self.CONFIG_SECRET_COMMON_FILE = os.path.join(self.CONFIG_SECRET_DIR,
                                                      'settings_common.json')
        self.CONFIG_SECRET_DEBUG_FILE = os.path.join(self.CONFIG_SECRET_DIR, 'settings_debug.json')
        self.CONFIG_SECRET_DEPLOY_FILE = os.path.join(self.CONFIG_SECRET_DIR,
                                                      'settings_deploy.json')
        self.make_and_copy_config_files()

        self.CONFIG_PUBLIC = json.loads(open(self.CONFIG_PUBLIC_FILE).read())
        self.CONFIG_SECRET_COMMON = json.loads(open(self.CONFIG_SECRET_COMMON_FILE).read())
        self.CONFIG_SECRET_DEBUG = json.loads(open(self.CONFIG_SECRET_DEBUG_FILE).read())
        self.CONFIG_SECRET_DEPLOY = json.loads(open(self.CONFIG_SECRET_DEPLOY_FILE).read())

        # Django paths
        self.DJANGO_DIR = os.path.join(self.PROJECT_DIR, 'django_app')
        self.DJANGO_CONFIG_DIR = os.path.join(self.DJANGO_DIR, 'config')
        self.DJANGO_SETTINGS_DIR = os.path.join(self.DJANGO_CONFIG_DIR, 'settings')

    def execute(self, rebuild=False):
        # Settings build variables
        self.print_intro()
        self.make_and_copy_config_files()
        # self.select_mode()
        # self.input_key(rebuild)
        # self.write_dict_to_file()
        # self.encrypt_secret()
        print()

    def make_and_copy_config_files(self):
        shutil.rmtree(self.PROJECT_DIR, '.config')
        shutil.copytree(
            os.path.join(self.PACKAGE_FILE_DIR, 'config'),
            os.path.join(self.PROJECT_DIR, '.config'),
        )
        # shutil.move(os.path.join(self.PACKAGE_FILE_DIR, 'config'), self.CONFIG_DIR)
        if not os.path.exists(self.CONFIG_SECRET_DIR):
            os.makedirs(self.CONFIG_SECRET_DIR)
        if not os.path.exists(self.CONFIG_SECRET_COMMON_FILE):
            open(self.CONFIG_SECRET_COMMON_FILE, 'wt').write('{}')
        if not os.path.exists(self.CONFIG_SECRET_DEBUG_FILE):
            open(self.CONFIG_SECRET_DEBUG_FILE, 'wt').write('{}')
        if not os.path.exists(self.CONFIG_SECRET_DEPLOY_FILE):
            open(self.CONFIG_SECRET_DEPLOY_FILE, 'wt').write('{}')

    def input_key(self, rebuild):
        # Public config - docker
        self.dict_key_make(config_public, 'docker')
        self.input_dict_value(
            msg='Dockerfile base name',
            dic=config_public['docker'],
            key='DockerfileBaseName',
        )
        self.input_dict_value(
            msg='Docker root image name (FROM)',
            dic=config_public['docker'],
            key='rootImageName',
        )
        # Public config - common
        self.dict_key_make(config_public, 'common')
        self.input_dict_value(
            msg='Application name',
            dic=config_public['common'],
            key='appName'
        )
        self.input_dict_value(
            msg='Default DB name',
            dic=config_public['common'],
            key='defaultDBName'
        )

        # Common secret config - docker
        self.dict_key_make(config_secret_common, 'docker')
        self.input_dict_value(
            msg='DockerImage Maintainer Email',
            dic=config_secret_common['docker'],
            key='maintainer'
        )

        # Common secret config - GitHub
        self.dict_key_make(config_secret_common, 'github')
        self.input_dict_value(
            msg='GitHub username',
            dic=config_secret_common['github'],
            key='username'
        )
        self.input_dict_value(
            msg='GitHub password',
            dic=config_secret_common['github'],
            key='password'
        )

        # Common secret config - Django
        self.dict_key_make(config_secret_common, 'django')
        self.dict_key_make(config_secret_common['django'], 'default_superuser')
        self.input_dict_value(
            msg='Django default superuser username',
            dic=config_secret_common['django']['default_superuser'],
            key='username'
        )
        self.input_dict_value(
            msg='Django default superuser password',
            dic=config_secret_common['django']['default_superuser'],
            key='password'
        )
        self.input_dict_value(
            msg='Django default superuser email',
            dic=config_secret_common['django']['default_superuser'],
            key='email',
            default='',
        )

        # Debug secret config - Django
        self.dict_key_make(config_secret_debug, 'django')
        self.input_dict_value(
            msg='[Debug] Django allowed hosts (default: ["*"])',
            dic=config_secret_debug['django'],
            key='allowed_hosts',
            default=['*', ],
        )
        # Debug secret config - Django - Database
        self.dict_key_make(config_secret_debug['django'], 'databases')
        self.dict_key_make(config_secret_debug['django']['databases'], 'default')
        db_engine = self.input_dict_value(
            msg='[Debug] DB Engine (default: postgresql_psycopg2)',
            dic=config_secret_debug['django']['databases']['default'],
            key='ENGINE',
            base='django.db.backends.',
            default='postgresql_psycopg2',
        )
        if 'sqlite3' in db_engine:
            sqlite_db_name = os.path.join(BASE_DIR, 'db.sqlite3')
            self.input_dict_value(
                msg='[Debug] DB Name (default: %s)' % sqlite_db_name,
                dic=config_secret_debug['django']['databases']['default'],
                key='NAME',
                default=sqlite_db_name,
            )
        else:
            self.input_dict_value(
                msg='[Debug] DB Name (default: %s)' % config_public['common']['defaultDBName'],
                dic=config_secret_debug['django']['databases']['default'],
                key='NAME',
                default='api-ios',
            )
            self.input_dict_value(
                msg='[Debug] DB Host (default: localhost)',
                dic=config_secret_debug['django']['databases']['default'],
                key='HOST',
                default='localhost'
            )
            self.input_dict_value(
                msg='[Debug] DB Port (default: 5432)',
                dic=config_secret_debug['django']['databases']['default'],
                key='PORT',
                default='5432'
            )
            self.input_dict_value(
                msg='[Debug] DB User',
                dic=config_secret_debug['django']['databases']['default'],
                key='USER',
            )
            self.input_dict_value(
                msg='[Debug] DB Password',
                dic=config_secret_debug['django']['databases']['default'],
                key='PASSWORD',
            )

        if self.mode == 'deploy':
            # Deploy secret config - Databases
            self.dict_key_make(config_secret_deploy['django'], 'databases')
            self.dict_key_make(config_secret_deploy['django']['databases'], 'default')
            self.input_dict_value(
                msg='[Deploy] DB Engine (default: postgresql_psycopg2)',
                dic=config_secret_deploy['django']['databases']['default'],
                key='ENGINE',
                base='django.db.backends.',
                default='postgresql_psycopg2',
            )
            self.input_dict_value(
                msg='[Deploy] DB Name',
                dic=config_secret_deploy['django']['databases']['default'],
                key='NAME',
            )
            self.input_dict_value(
                msg='[Deploy] DB Host',
                dic=config_secret_deploy['django']['databases']['default'],
                key='HOST',
            )
            self.input_dict_value(
                msg='[Deploy] DB Port (default: 5432)',
                dic=config_secret_deploy['django']['databases']['default'],
                key='PORT',
                default='5432'
            )
            self.input_dict_value(
                msg='[Deploy] DB User',
                dic=config_secret_deploy['django']['databases']['default'],
                key='USER',
            )
            self.input_dict_value(
                msg='[Deploy] DB Password',
                dic=config_secret_deploy['django']['databases']['default'],
                key='PASSWORD',
            )

            # Deploy secret config - AWS
            self.dict_key_make(config_secret_deploy, 'aws')
            self.input_dict_value(
                msg='[Deploy] AWS AccessKeyId',
                dic=config_secret_deploy['aws'],
                key='access_key_id',
            )
            self.input_dict_value(
                msg='[Deploy] AWS SecretAccessKey',
                dic=config_secret_deploy['aws'],
                key='secret_access_key',
            )
            self.input_dict_value(
                msg='[Deploy] AWS S3 Bucket name',
                dic=config_secret_deploy['aws'],
                key='s3_bucket_name',
            )
            self.input_dict_value(
                msg='[Deploy] AWS S3 Region name',
                dic=config_secret_deploy['aws'],
                key='s3_region_name',
            )

    @staticmethod
    def write_dict_to_file():
        with open(CONF_SECRET_COMMON_FILE, 'wt') as f:
            f.write(json.dumps(config_secret_common, indent=4, sort_keys=True))
        with open(CONF_SECRET_DEBUG_FILE, 'wt') as f:
            f.write(json.dumps(config_secret_debug, indent=4, sort_keys=True))

    @staticmethod
    def encrypt_secret():
        encrypt_command = 'tar cvf secrets.tar .conf_secret &&' \
                          'travis encrypt-file secrets.tar --add &&' \
                          'git add secrets.tar.enc .travis.yml'
        subprocess.run(encrypt_command, shell=True)
        print(' encrypt secret config')

    @staticmethod
    def print_intro():
        intro_string = '=== SettingsBuild ==='
        print(intro_string)

    def select_mode(self):
        print(' Select setting mode (default: 1.Debug)')
        print('  1.Debug')
        print('  2.Deploy')
        val = input('   > Select: ')
        if val == '2':
            self.mode = 'deploy'
        else:
            self.mode = 'debug'

    @staticmethod
    def dict_key_make(dic, key):
        """
        dic에 key에 해당하는 dict가 없을 경우 생성해줌
        :param dic: dict
        :param key: dic에 추가할 dict의 key
        :return:
        """
        if not dic.get(key):
            dic[key] = {}

    @staticmethod
    def input_dict_value(msg, dic, key, base='', default=None):
        """
        아래의 조건동안 dic으로 전달된 dict에 넣을 값을 입력받는다
        매 입력마다 msg의 값을 출력해준다
            1. 해당 키 값이 없거나
            2. 키의 타입이 str이며 양쪽 여백을 없앤 결과(.strip())가 공백인 경우
        :param msg: 어떤 키에 값을 넣을것인지 메시지 출력
        :param dic: 실제로 값을 기록할 dict
        :param key: dict에서 값을 기록할 key
        :param default: 입력되지 않을 경우 기본적으로 넣을 값
        :return: 입력된 값
        """
        while not dic.get(key) or (isinstance(dic[key], str) and dic[key].strip() == ''):
            value = base + input('{}: '.format(msg)).strip()
            dic[key] = value
            if default and value == '':
                dic[key] = default
        return dic[key]
