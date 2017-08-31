import json
import os
import re
import subprocess

from .cls import *


class DockerBuild:
    def __init__(self, project_name):
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

        # Docker build variables
        self.categories = []
        self.root_image_name = self.CONFIG_PUBLIC['docker']['DockerfileBaseName']
        self.start_image = None
        self.end_image = None
        self.is_production = False
        conf_dir = self.CONFIG_DOCKER_DIR
        re_compile_category = re.compile(r'^([0-9]+)\.(.*)')
        docker_conf_listdir = os.listdir(conf_dir)

        for category in docker_conf_listdir:
            if os.path.isdir(os.path.join(conf_dir, category)):
                cur_category = DockerCategory(
                    base_image_name=self.root_image_name,
                    order=re_compile_category.search(category).group(1),
                    title=re_compile_category.search(category).group(2),
                    path=os.path.join(self.CONFIG_DOCKER_DIR, category),
                )
                self.categories.append(cur_category)

        self.print_intro()
        self.set_options()
        self.set_start_image()
        self.set_end_image()
        self.make_dockerfiles()

    def make_and_copy_config_files(self):
        if not os.path.exists(self.CONFIG_DOCKER_DIR):
            os.makedirs(self.CONFIG_DOCKER_DIR)
        if not os.path.exists(self.CONFIG_SECRET_DIR):
            os.makedirs(self.CONFIG_SECRET_DIR)
        if not os.path.exists(self.CONFIG_SECRET_COMMON_FILE):
            open(self.CONFIG_SECRET_COMMON_FILE, 'wt').write('{}')
        if not os.path.exists(self.CONFIG_SECRET_DEBUG_FILE):
            open(self.CONFIG_SECRET_DEBUG_FILE, 'wt').write('{}')
        if not os.path.exists(self.CONFIG_SECRET_DEPLOY_FILE):
            open(self.CONFIG_SECRET_DEPLOY_FILE, 'wt').write('{}')

    @staticmethod
    def print_intro():
        intro_string = '=== DockerBuild ==='
        print(intro_string)

    def set_options(self):
        for category in self.categories:
            category.select_options()

    @property
    def selected_options(self):
        """
        각 카테고리(template, base, common, extra)의
        옵션 (00, 01, 02...등)에
        선택한 서브옵션 (03.extra - 01 - debug or production)들로 이루어진 리스트를 리턴
        서브옵션이 선택되지 않았을 경우 None이 원소로 반환됨
        :return: list(DockerCategorySubOption)
        """
        return [option.selected_sub_option for category in self.categories for option in
                category.options]

    @property
    def is_selected_all_sub_options(self):
        """
        모든 카테고리의 옵션에 대해 서브옵션을 선택했는지 여부 반환
        :return: Bool, 모든 서브옵션을 선택했는지
        """
        return all(self.selected_options)

    def set_start_image(self):
        select_string = 'Select start image:\n'
        select_string += '  {}.{}\n'.format(
            0, self.CONFIG_PUBLIC['docker']['rootImageName'],
        )
        for index, option in enumerate(self.selected_options):
            select_string += '  {}.{}\n'.format(
                index + 1,
                option.info
            )
        select_string = select_string[:-1]
        while True:
            print(select_string)
            selected_option_index = input(
                '  > Select image number (default: {}.{}): '.format(
                    0, self.CONFIG_PUBLIC['docker']['rootImageName']
                )
            )
            try:
                if selected_option_index == '' or selected_option_index == '0':
                    self.start_image = None
                else:
                    self.start_image = self.selected_options[int(selected_option_index) - 1]
                print('')
                break
            except ValueError as e:
                print('  ! Input value error ({})\n'.format(e))
            except IndexError as e:
                print('  ! Selected SubOption index is not valid ({})\n'.format(e))

    def set_end_image(self):
        start_index = self.selected_options.index(self.start_image) if self.start_image else 0
        select_string = 'Select end image:\n'
        for index, option in enumerate(self.selected_options):
            if index < start_index:
                continue
            select_string += '  {}.{}\n'.format(
                index + 1,
                option.info
            )
        select_string = select_string[:-1]
        while True:
            print(select_string)
            default_index = len(self.selected_options) - 1
            selected_option_index = input(
                '  > Select image number (default: {}.{}): '.format(
                    default_index + 1,
                    self.selected_options[default_index].info
                )
            )
            try:
                if selected_option_index == '':
                    selected_option_index = default_index + 1
                int_selected_option_index = int(selected_option_index) - 1
                self.end_image = self.selected_options[int_selected_option_index]
                print('')
                # 만약 선택된 index가 default_index(마지막 인덱스)와 같을 경우 (끝 이미지를 선택한 경우)
                # is_production을 True로 설정하고,
                # 이후 make_dockerfiles에서 프로젝트폴더에 Dockerfile을 생성해준다.
                if int_selected_option_index == default_index:
                    self.is_production = True
                break
            except ValueError as e:
                print('  ! Input value error ({})\n'.format(e))
            except IndexError as e:
                print('  ! Selected SubOption index is not valid ({})\n'.format(e))

    def make_dockerfiles(self):
        start_index = self.selected_options.index(self.start_image) if self.start_image else None
        end_index = self.selected_options.index(self.end_image)
        root_image_name = self.CONFIG_PUBLIC['docker']['rootImageName']

        template = open(os.path.join(self.CONFIG_DOCKER_DIR, 'template.docker')).read()
        print('== Make Dockerfiles ==')
        # self.PROJECT_DIR부터 .dockerfiles디렉토리 생성 (임시 Dockerfile들 저장소)
        os.makedirs(os.path.join(self.PROJECT_DIR, '.dockerfiles'), exist_ok=True)
        dockerfiles_dir = os.path.join(self.PROJECT_DIR, '.dockerfiles')
        for index, option in enumerate(self.selected_options):
            if (start_index and index < start_index) or index > end_index:
                continue
            file_name = 'Dockerfile.{}.{}.{}.{}'.format(
                option.parent_option.category.order,
                option.parent_option.category.title,
                option.parent_option.order,
                option.title)
            print(file_name)
            prev_image = self.selected_options[index - 1].info if index > 0 else root_image_name
            cur_template = template.format(
                from_image=prev_image,
                maintainer=self.CONFIG_SECRET_COMMON['docker']['maintainer'],
                content=open(os.path.join(option.path), 'rt').read(),
            )
            open(os.path.join(dockerfiles_dir, file_name), 'wt').write(cur_template)
            # is_production일 경우 마지막 loop의 파일을 프로젝트폴더/Dockerfile에 기록
            if self.is_production and index == len(self.selected_options) - 1:
                cur_template = template.format(
                    from_image=self.CONFIG_PUBLIC['docker']['dockerHubImageName'],
                    maintainer=self.CONFIG_SECRET_COMMON['docker']['maintainer'],
                    content=open(os.path.join(option.path), 'rt').read(),
                )
                open(os.path.join(self.PROJECT_DIR, 'Dockerfile'), 'wt').write(cur_template)

            build_command_template = 'docker build . -t {name} -f {dockerfile_name}'
            build_command = build_command_template.format(
                name=option.info,
                dockerfile_name=os.path.join(dockerfiles_dir, file_name),
            )
            subprocess.run(build_command, shell=True)
