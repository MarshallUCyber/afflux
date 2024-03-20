import inspect
import os
import pkgutil
import utilities
from colorama import reinit, Fore

reinit()  # Colorama
utils = utilities.Utilities.get_instance()


class Plugin(object):
    """
    Base class that each plugin must inherit from. within this class
    you must define the methods that all of your plugins must implement
    """

    def __init__(self):
        self.name = 'UNKNOWN'
        self.description = 'UNKNOWN'

    def help(self):
        """
        A help program that we expect all plugins to implement.
        """
        raise NotImplementedError

    def setup_arg_parser(self, plugin_args, parent_args, parent_parser):
        """
        A help program that we expect all plugins to implement.
        """
        raise NotImplementedError

    def run(self):
        """
        The method that we expect all plugins to implement. This is the
        method that our framework will call
        """
        raise NotImplementedError


class PluginCollection(object):
    """
        Upon creation, this class will read the plugins package for modules
        that contain a class definition that is inheriting from the Plugin class
    """

    def __init__(self, plugin_package, verbose):
        """
            Constructor that initiates the reading of all available plugins
            when an instance of the PluginCollection object is created
        """
        self.seen_paths = None
        self.plugins = None
        self.verbose = verbose
        self.plugin_package = plugin_package
        self.reload_plugins()

    def reload_plugins(self):
        """
            Reset the list of all plugins and initiate the walk over the main
            provided plugin package to load all available plugins
        """
        self.plugins = []
        self.seen_paths = []
        if self.verbose:
            utils.multi_print(f"{Fore.GREEN}\n[*] Looking for plugins: {self.plugin_package}", worker=False)
        self.walk_package(self.plugin_package)
        utils.multi_print("\n", worker=False)

    def list_plugins(self):
        """
            Return a list of all plugins.
        """
        plugin_list = []
        for plugin in self.plugins:
            plugin_list.append(plugin)
        return plugin_list

    def return_plugin(self, plugin_name):
        """
            When given a plugin name, return a handle to that plugin.
        """
        for plugin in self.plugins:
            if plugin_name == plugin.name:
                return plugin
        return False

    def walk_package(self, package):
        """
            Recursively walk the supplied package to retrieve all plugins
        """
        imported_package = __import__(package, fromlist=['blah'])

        for _, plugin_name, is_pkg in pkgutil.iter_modules(imported_package.__path__, imported_package.__name__ + '.'):
            if not is_pkg:
                plugin_module = __import__(plugin_name, fromlist=['blah'])
                cls_members = inspect.getmembers(plugin_module, inspect.isclass)
                for (_, c) in cls_members:
                    # Only add classes that are a subclass of Plugin, but NOT Plugin itself
                    if issubclass(c, Plugin) & (c is not Plugin):
                        if self.verbose:
                            utils.multi_print(f"{Fore.GREEN}\tFound plugin class: {Fore.RESET} "
                                              f"{c.__module__}.{c.__name__}", worker=False)
                        self.plugins.append(c())

        # Now that we have looked at all the modules in the current package, start looking
        # recursively for additional modules in sub packages
        all_current_paths = []
        if isinstance(imported_package.__path__, str):
            all_current_paths.append(imported_package.__path__)
        else:
            all_current_paths.extend([x for x in imported_package.__path__])

        for pkg_path in all_current_paths:
            if pkg_path not in self.seen_paths:
                self.seen_paths.append(pkg_path)

                # Get all subdirectory of the current package path directory
                child_pkgs = [p for p in os.listdir(pkg_path) if os.path.isdir(os.path.join(pkg_path, p))]

                # For each subdirectory, apply the walk_package method recursively
                for child_pkg in child_pkgs:
                    self.walk_package(package + '.' + child_pkg)
