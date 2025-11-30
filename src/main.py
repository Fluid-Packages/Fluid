import requests.exceptions

import installer, configrunner
from sys import argv

def show_help():
    print("""usage: fluid [install <package> / uninstall <package> / show]

These are common Fluid commands:

install package
\tfluid install <package>  |  install package from official source
\tfluid install <repository> <author>  |  install package from Github

uninstall package
\tfluid uninstall <package>  |  uninstall package

show all packages
\tfluid show  |  show all packages


| more on github
| https://github.com/Fluid-Packages/Fluid

||||| by i4ego
    """)

match len(argv):
    case 3:
        match argv[1]:
            case "install":
                try:
                    install_configs = installer.install(argv[2])
                except requests.exceptions.HTTPError:
                    print("Package not found :(")
                    raise SystemExit
                except requests.exceptions.ConnectionError:
                    print("Connection error :(")
                    raise SystemExit
                configrunner.run(install_configs, argv[2])
            case "uninstall":
                try:
                    installer.uninstall(argv[2])
                except FileNotFoundError:
                    print("Package not found :(")
                    raise SystemExit
            case _:
                show_help()
                raise SystemExit
    case 4:
        match argv[1]:
            case "install":
                try:
                    install_configs = installer.install(argv[2], author=argv[3])
                except requests.exceptions.HTTPError:
                    print("Package not found :(")
                    raise SystemExit
                except requests.exceptions.ConnectionError:
                    print("Connection error :(")
                    raise SystemExit
                configrunner.run(install_configs, argv[2])
            case _:
                show_help()
                raise SystemExit
    case _:
        show_help()
        raise SystemExit
