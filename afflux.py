# By Marshall University on 7/10/2021

import argparse
from datetime import datetime
from os import path, chdir, getcwd, environ
from sys import exit

from colorama import init, deinit, Fore

import imaging
from plugin_manager import PluginCollection

init(autoreset=True)

text_art = r"""
_____/\\\\\\\\\_____/\\\\\\\\\\\\\\\__/\\\\\\\\\\\\\\\__/\\\______________/\\\________/\\\__/\\\_______/\\\_        
 ___/\\\\\\\\\\\\\__\/\\\///////////__\/\\\///////////__\/\\\_____________\/\\\_______\/\\\_\///\\\___/\\\/__       
  __/\\\/////////\\\_\/\\\_____________\/\\\_____________\/\\\_____________\/\\\_______\/\\\___\///\\\\\\/____      
   _\/\\\_______\/\\\_\/\\\\\\\\\\\_____\/\\\\\\\\\\\_____\/\\\_____________\/\\\_______\/\\\_____\//\\\\______     
    _\/\\\\\\\\\\\\\\\_\/\\\///////______\/\\\///////______\/\\\_____________\/\\\_______\/\\\______\/\\\\______    
     _\/\\\/////////\\\_\/\\\_____________\/\\\_____________\/\\\_____________\/\\\_______\/\\\______/\\\\\\_____   
      _\/\\\_______\/\\\_\/\\\_____________\/\\\_____________\/\\\_____________\//\\\______/\\\_____/\\\////\\\___  
       _\/\\\_______\/\\\_\/\\\_____________\/\\\_____________\/\\\\\\\\\\\\\\\__\///\\\\\\\\\/____/\\\/___\///\\\_ 
        _\///________\///__\///______________\///______________\///////////////_____\/////////_____\///_______\///__
        
        Version 1.1"""


def main():
    parser = argparse.ArgumentParser(description=f"{Fore.GREEN}AFF4 logical imager.{Fore.RESET}",
                                     formatter_class=argparse.RawTextHelpFormatter, add_help=False)

    # General command line options
    parser.add_argument('-h', "--help", action="store_true",
                        help='print help output.')
    parser.add_argument('-v', "--verbose", action="store_true", default=False,
                        help='enable verbose output.')
    parser.add_argument('-t', "--temp", nargs=1, action="store", metavar='PATH',
                        help='directory to create any temporary files.')
    parser.add_argument('-A', "--append", action="store_true", default=False,
                        help='append to an existing AFF4 image specified with `-o`.')
    parser.add_argument('-e', "--container_password", nargs=1, action="store", metavar='PASSWORD',
                        help='password to create an encrypted AFF4 container.')
    parser.add_argument('-o', "--output", nargs=1, action="store", metavar='OUTPUT_FILE',
                        help='output AFF4 file name.')
    parser.add_argument("--overwrite", action="store_true", default=False,
                        help='overwrite AFF4 file if it already exists.')
    parser.add_argument('-m', "--meta", action="store", nargs=1, metavar='AFF4_IMAGE',
                        help='print the AFF4 image\'s metadata.', )
    parser.add_argument('-p', "--plugin", action="store", nargs=1, metavar='PLUGIN_NAME',
                        help='specify a plugin to load, or use "list" to list all plugins.', )
    parser.add_argument("-z", "--zip", action="store_true", default=False,
                        help='write to a Zip container instead of AFF4.')

    # Temporarily set 'QT_STYLE_OVERRIDE' environment variable to suppress QT warnings on some systems.
    environ["QT_STYLE_OVERRIDE"] = ""

    print(f"{Fore.GREEN}{text_art}\n")
    print(f"{Fore.GREEN}\n\n[+] Afflux Logical Imager Starting...")
    args, extra_args = parser.parse_known_args()
    plugins = PluginCollection('plugins', args.verbose)
    imager = imaging.Imager(args.verbose)
    imager.check_os()
    if args.verbose:
        print(f"{Fore.GREEN}[*] OS: {Fore.RESET}{imager.os}")
    current_path = getcwd()

    if args.plugin is not None:
        parser.add_argument('-x', "--extract", action="store", nargs=1, metavar='AFF4_IMAGE',
                            help=f'extract all files and folders from an AFF4 image.\n\n{Fore.GREEN}[Plugin Options]'
                                 f'{Fore.RESET}\n')
    else:
        parser.add_argument('-x', "--extract", action="store", nargs=1, metavar='AFF4_IMAGE',
                            help='extract all files and folders from an AFF4 image.\n\n')

    args, extra_args = parser.parse_known_args()
    # Print help for '-h' and no plugin argument.
    if args.help and args.plugin is None:
        parser.print_help()
        exit()

    # Also print help if nothing is given.
    if not any(vars(args).values()):
        print(parser.format_help())
        exit()

    # Print container metadata
    if args.meta:
        if path.exists(args.meta[0]):
            print(f"{Fore.GREEN}[+] Loading image...")
            imager.meta(args.meta[0], args.container_password)
            exit()
        else:
            print(f"{Fore.RED}[-] File not found: {Fore.RESET}{args.meta[0]}\n")
            exit()

    # Print help if no -p switch is used.
    if args.plugin is None and args.extract is None:
        parser.print_help()
        exit()

    # If '-p' is 'list', list plugins.
    if args.plugin:
        if args.plugin[0].lower() == 'list':
            plugin_list = plugins.list_plugins()
            print(f"{Fore.GREEN}\n[+] Plugins:\n")
            for plugin in plugin_list:
                print(f"{plugin.name} \t| {plugin.description}")
            print()
            exit()

    # Check to make sure '.aff4' or '.zip' is prepended to the output. If not, add it.
    if args.output:
        if not args.extract:
            if not args.zip:
                if args.output[0][-5:] != ".aff4":
                    args.output = [args.output[0] + ".aff4"]
            else:
                if args.output[0][-4:] != ".zip":
                    args.output = [args.output[0] + ".zip"]

    # TODO: Should we check this here?
    # Check if an output file is given with a plugin.
    if args.plugin:
        if not args.help:
            if not args.output:
                print(f"{Fore.RED}[-] No output file given. Use '-o' to specify an output file. "
                      f"To see options, use '-h'.\n")
                exit()

    # Check if the file already exists
    if args.output:
        if not args.extract:
            if not args.append:
                if not args.overwrite:
                    if path.exists(args.output[0]):
                        print(f"{Fore.GREEN}[*] '{args.output[0]}' already exists. Overwrite? (y/n)")
                        overwrite = input("> ").lower().strip()
                        if (overwrite == "y") or (overwrite == "yes"):
                            pass
                        else:
                            exit()
            else:
                # Check if the file we are appending to exists.
                if not path.exists(args.output[0]):
                    print(f"{Fore.RED}[-] '{args.output[0]}' does not exist.")
                    exit()

    start_time = datetime.now()
    try:
        # Cleanup anything if needed.
        clean = imager.cleanup(specified_path=args.temp)
        if not clean:
            exit()

        # Try and load the specified plugin.
        if args.plugin is not None:
            plugin = plugins.return_plugin(args.plugin[0])
            if plugin is not False:
                plugin.setup_arg_parser(extra_args, args, parser)
                if args.help:
                    plugin.parser.print_help()
                else:
                    plugin.run()
            else:
                print(f"{Fore.RED}[-] Plugin not found.\n")
                exit()

        # Extract files from the container
        elif args.extract:
            print(f"{Fore.GREEN}[*] Preparing to extract.")
            if not path.isfile(args.extract[0]):
                print(f"{Fore.RED}[-] AFF4 file not found: {Fore.RESET}{args.extract[0]}\n")
                exit()
            if not args.output:
                print(f"{Fore.RED}[-] Specify output directory with '-o'.\n")
                exit()
            imager.extract_all(args.extract[0], args.output[0], args.container_password)
        print(f"{Fore.GREEN}\n[*] Time: {Fore.RESET}{str(datetime.now() - start_time)}\n")

    except KeyboardInterrupt:
        print(f"{Fore.GREEN}\n[*] Attempting to quit gracefully...")
        chdir(current_path)
        imager.cleanup(specified_path=args.temp)
        exit()

    except FileExistsError as e:
        if args.verbose:
            print(e)
        print(f"{Fore.RED}\n[-] Need to clean up errors from last run. Please run again...")
        chdir(current_path)
        imager.cleanup(specified_path=args.temp)
        exit()


if __name__ == "__main__":
    main()
    deinit()                # De-initialize colorama
