# By Marshall University on 2/12/2023
# Pull data from HTTP and toss it in an AFF4 container.

import argparse

from colorama import reinit, Fore
from os import path, listdir, chdir, mkdir
from requests import get
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup

import imaging
import plugin_manager
import utilities

reinit()  # Colorama
utils = utilities.Utilities.get_instance()


class HttpImage(plugin_manager.Plugin):
    """
        This class is used to image a folder or files via http.
    """

    def __init__(self):
        """
            Constructor for Http Imager Plugin.
        """
        super().__init__()
        # Values used to select the plugin and show a description of the plugin.
        self.name = "generic_http"
        self.description = "Image a file or folder via http."

        # Variables used by the plugin.
        self.arguments = None
        self.parser = None
        self.imager = None
        self.temp = None
        self.base_urls = []

    def generate_links(self, response):
        """
            Get the links from the response.
        """

        urls = []
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            url = link.get('href')
            if url.strip() == "/":
                continue
            urls.append(url)
        return urls

    def download_dir(self, links, output, recursive, chunk_size):
        """
            Recursively download files and folders from a web directory
        """
        # TODO: Think about infinite loops?
        for url in links:
            try:
                response = get(url)
                for item in self.generate_links(response):
                    item_url = url + item
                    item_dst = utils.check_file_names(path.join(output, item))

                    # Folders
                    if item.endswith('/'):
                        if recursive:
                            mkdir(unquote(item_dst))
                            self.download_dir([item_url], item_dst, recursive, chunk_size)
                    # Files
                    else:
                        if self.arguments.verbose:
                            utils.multi_print(f"\t{Fore.GREEN}Downloading: {Fore.RESET}{item_url}")
                        r = get(item_url, stream=True)
                        with open(unquote(item_dst), 'wb') as f:
                            for chunk in r.iter_content(chunk_size):
                                if chunk:
                                    f.write(chunk)
            except Exception as e:
                if "[Errno 111] Connection refused" in str(e):
                    utils.multi_print(f"{Fore.RED}[-] Could not connect to: {Fore.RESET}{url}")
                    return False
                elif "[Errno 13] Permission denied" in str(e):
                    utils.multi_print(f"\t{Fore.RED}Permission denied: {Fore.RESET}{url}")
                    pass
                elif "Invalid URL" in str(e):
                    utils.multi_print(f"\t{Fore.RED}Invalid URL: {Fore.RESET}{url}")
                    pass
                else:
                    utils.multi_print(e)
                    return False
        return True

    def http_image(self):
        self.imager = imaging.Imager(self.arguments.verbose, zip=self.arguments.zip)
        output_path, old_path, tmp_path = self.imager.setup_tmp_directory(self.arguments.temp, self.arguments.output[0])
        chdir(tmp_path)

        # Get base urls, so we can check and make sure we stay within the same domain.
        for link in self.arguments.link:
            self.base_urls.append(urlsplit(link).netloc)

        # Download the directories.
        result = self.download_dir(self.arguments.link, tmp_path, self.arguments.recursive,
                                   int(self.arguments.chunk_size[0]))

        # If it succeeds, toss it in an AFF4.
        if result:
            directories = listdir()
            self.imager.add_path_names(output_path, directories, True, self.arguments.append,
                                       self.arguments.container_password)
        chdir(old_path)
        return result

    def setup_arg_parser(self, plugin_args, parent_args, parent_parser):
        """
            Setup arguments required by the plugin. Any arguments not recognized as default Afflux arguments are passed
            as `plugin_args`.
        """

        # Setup parser to include parent arguments.
        self.parser = argparse.ArgumentParser(parents=[parent_parser],
                                              description=f"{Fore.GREEN}HTTP Imaging Plugin{Fore.RESET}",
                                              formatter_class=argparse.RawTextHelpFormatter,
                                              add_help=False)
        self.parser.add_argument('-l', "--link", action="store", nargs="*", metavar='LINK',
                                 help='create image from a link.')
        self.parser.add_argument('-c', "--chunk-size", action="store", nargs="*", default=[1024], type=int,
                                 help='chunk size to download with. Default is 1024.')
        self.parser.add_argument('-r', "--recursive", action="store_true", default=False,
                                 help='add files and folders recursively.')

        # Parse afflux and plugin arguments, and store them in `self.arguments`.
        self.arguments, extra = self.parser.parse_known_args(plugin_args, parent_args)
        return True

    def run(self):
        utils.multi_print(f"{Fore.GREEN}[+] Loaded HTTP Imaging plugin.")
        if self.arguments.link:
            return self.http_image()
        else:
            self.parser.print_help()
            return False
