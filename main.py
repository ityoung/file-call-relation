from glob import glob
import os
from functools import reduce


class ModuleImportFinder(object):
    def __init__(self, mod_name):
        self.find_next_line = False
        self.parent_module = None
        self.modules = []
        self.mod_name = mod_name

    def find_modules(self, code):
        """
        find modules with import or from at beginning of line, and cover all possible.
        :param code: python code in an open file.
        :return: 
        """
        code = code.splitlines()
        for item in code:
            # pass all comment and blank line.
            if not item or item[0] == '#':
                continue
            if self.find_next_line is True:
                self.find_modules_next_line(item, self.parent_module)
            item_import_head = item[:7]
            item_import_tail = item[7:]
            item_from_head = item[:5]
            item_from_tail = item[5:]
            if item_import_head == "import ":
                self.parent_module = None
                if '\\' in item[-1]:
                    self.find_next_line = True
                if ',' in item_import_tail:
                    self.modules += item_import_tail.strip("\\").replace(" ", "").split(",")
                else:
                    self.modules.append(item_import_tail.strip("\\").replace(" ", ""))
            if item_from_head == "from ":
                if '\\' in item[-1]:
                    self.find_next_line = True
                module = item_from_tail.split('import')
                self.parent_module = module[0].strip(" ")
                self.set_absolute_path()
                item_from_tail = module[1]
                if ',' in item_from_tail:
                    modules = item_from_tail.strip("\\").replace(" ", "").split(",")
                    self.modules += map(lambda item: self.parent_module + "." + item, modules)
                else:
                    self.modules.append(self.parent_module + "." + item_from_tail.strip("\\").replace(" ", ""))

    def find_modules_next_line(self, code, module=None):
        """

        :param code: line to find modules
        :param module: parent module name
        :return: 
        """
        if '\\' not in code[-1]:
            self.find_next_line = False
        code = code.strip("\\").replace(" ", "")
        if ',' in code:
            # split all modules/functions/classes
            modules = code.replace(" ", "").split(",")
            if module:
                # add parent module name as splited modules' head
                modules = map(lambda x: module + "." + x, modules)
            self.modules += modules
        else:
            if module:
                code = module + "." + code
            self.modules.append(code)

    def set_absolute_path(self):
        """Recursive convert '.' of relative path to absolute path."""
        parent_module_tail = self.parent_module.strip(".")
        length = len(self.parent_module) - len(parent_module_tail)
        if length == 0:
            return
        abs_mod_list = self.mod_name.split(".")
        head = abs_mod_list[:-length]
        # link absolute base path to relative path tail.
        self.parent_module = reduce(lambda x, y: x + '.' + y, head) + "." + parent_module_tail


class FileCallGenerator(object):
    def __init__(self, filepath):
        self.file_path = filepath

    def get_module_name(self, filename):
        """Try to determine the full module name of a source file, by figuring out
        if its directory looks like a package (i.e. has an __init__.py file)."""

        init_path = os.path.join(os.path.dirname(filename), '__init__.py')
        mod_name = os.path.basename(filename).replace('.py', '')

        if not os.path.exists(init_path):
            return mod_name

        if not os.path.dirname(filename):
            return mod_name

        return self.get_module_name(os.path.dirname(filename)) + '.' + mod_name

    def get_module_list(self):
        """Find all file mached file_path."""
        self.module_list = []
        for filename in self.file_path:
            mod_name = self.get_module_name(filename)
            self.module_list.append(mod_name)
        return self.module_list

    def find_files(self, mod_name):
        """Receive a mod_name, and recursive figure the file name instead of 
        function/class name."""
        if mod_name in self.module_list:
            return mod_name
        elif "." in mod_name:
            mod_name_list = mod_name.split(".")
            mod_name = reduce(lambda x, y: x + '.' + y, mod_name_list[:-1])
            return self.find_files(mod_name)
        else:
            return False

    def generate_call_rel(self):
        """Generate files calling relation."""
        self.call_rel = {}
        for filename in self.file_path:
            mod_name = self.get_module_name(filename)
            with open(filename, "rt", encoding="utf-8") as f:
                content = f.read()
            finder = ModuleImportFinder(mod_name)
            finder.find_modules(content)
            found = set()
            for item in finder.modules:
                res = self.find_files(item)
                if res is False:
                    continue
                else:
                    found.add(res)
            self.call_rel[mod_name] = list(found)
        return self.call_rel


if __name__ == '__main__':
    path_base = YOUR_PROJECT_PATH
    # only find python file
    args = [path_base + "/*.py", path_base + "/*/*.py", path_base + "/*/*/*.py"]
    filenames = [fn2 for fn in args for fn2 in glob(fn)]
    file_an = FileCallGenerator(filenames)
    print(file_an.get_module_list())
    print(file_an.generate_call_rel())
