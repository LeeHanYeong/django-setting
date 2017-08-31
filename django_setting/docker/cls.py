import os
import re

__all__ = (
    'DockerCategory',
    'DockerCategoryOption',
    'DockerCategorySubOption',
)


class DockerCategory:
    def __init__(self, base_image_name, order, title, path, options=None):
        self.base_image_name = base_image_name
        self.order = order
        self.title = title
        self.path = path
        self.options = []

        re_compile_option = re.compile(r'^([0-9]+)\.(.*)\.docker')

        option_listdir = os.listdir(self.path)
        # 각 카테고리(00.template, 01.base...)내의 파일들을 순회
        for option in option_listdir:
            # 03.extra의 01.debug, 01.production...도 순회
            cur_option_order = re_compile_option.search(option).group(1)
            # Option인스턴스의 order가 cur_option_order(00, 01등)과 같은 Option이 self.options리스트 목록에 없을 경우 새로 만들어 줌
            if not any(option.order == cur_option_order for option in self.options):
                cur_option = DockerCategoryOption(category=self, order=cur_option_order)
                self.options.append(cur_option)
            # 같은 옵션번호를 가질 경우 cur_option은 같은 DockerCategoryOption객체를 사용
            cur_option = next(
                (option for option in self.options if option.order == cur_option_order), None)
            # 파일 하나하나가 서브옵션이므로 각 루프마다 서브옵션을 생성, 추가
            cur_sub_option = DockerCategorySubOption(
                parent_option=cur_option,
                order=cur_option_order,
                title=re_compile_option.search(option).group(2)
            )
            cur_option.sub_options.append(cur_sub_option)

    def __str__(self):
        ret = 'DockerCategory({}.{})\n'.format(self.order, self.title)
        items = {
            'order': self.order,
            'title': self.title,
            'path': self.path,
            'options': self.options
        }
        for k, v in items.items():
            ret += '  {:10}: {}\n'.format(k, v)
        ret = ret[:-1]
        return ret

    @property
    def is_require_select_option(self):
        for option in self.options:
            if option.is_require_select_option:
                return True
        return False

    @property
    def unique_options(self):
        if self.is_require_select_option:
            raise Exception('require option select')
        return [sub_option for option in self.options for sub_option in option.sub_options]

    def select_options(self):
        for option in self.options:
            option.select_sub_option()


class DockerCategoryOption:
    def __init__(self, category, order, options=None):
        self.category = category
        self.order = order
        self.sub_options = options if options else []
        self.selected_sub_option = None

    def __repr__(self):
        return 'Option(Category:[{}], Order:[{}])'.format(
            self.category.title,
            self.order,
        )

    @property
    def is_require_select_option(self):
        if len(self.sub_options) > 1:
            return True
        return False

    @property
    def unique_sub_option(self):
        if self.is_require_select_option:
            raise Exception('require select sub option')
        else:
            return self.sub_options[0]

    def select_sub_option(self):
        self.selected_sub_option = None
        if self.is_require_select_option:
            select_string = 'Category({}.{})\n - Option({})\n -- SubOption select:\n'.format(
                self.category.order,
                self.category.title,
                self.order
            )
            for index, sub_option in enumerate(self.sub_options):
                select_string += '  {}.{}\n'.format(
                    index + 1,
                    sub_option.title
                )
            select_string = select_string[:-1]
            while True:
                print(select_string)
                selected_sub_option_index = input('  > Select SubOption: ')
                try:
                    selected_sub_option = self.sub_options[int(selected_sub_option_index) - 1]
                    self.selected_sub_option = selected_sub_option
                    print('')
                    break
                except ValueError as e:
                    print('  ! Input value error ({})\n'.format(e))
                except IndexError as e:
                    print('  ! Selected SubOption index is not valid ({})\n'.format(e))

        else:
            self.selected_sub_option = self.unique_sub_option
            # print('Don\'t need select SubOption. This Option has unique SubOption')
        return self.selected_sub_option


class DockerCategorySubOption:
    def __init__(self, parent_option, order, title):
        self.parent_option = parent_option
        self.order = order
        self.title = title

    def __repr__(self):
        return self.info

    @property
    def info(self):
        return '{}-{}-{}-{}'.format(
            self.parent_option.category.base_image_name,
            self.parent_option.category.title,
            self.parent_option.order,
            self.title
        )

    @property
    def path(self):
        return '{}/{}.{}.docker'.format(
            self.parent_option.category.path,
            self.order,
            self.title
        )
