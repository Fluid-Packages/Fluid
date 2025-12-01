import pathlib, sys, os

def run(install_configs: dict, repo: str):
    if "os" in install_configs:
        if "all" in install_configs["os"].split(" "):
            pass
        elif sys.platform not in install_configs["os"].split(" "):
            print("This package is not supporting your os.")
            raise SystemExit
    if "run_after_install" in install_configs:
        for x in install_configs["run_after_install"]:
            os.system(x)
    if "show_after_install" in install_configs:
        for x in install_configs["show_after_install"]:
            print(x.replace("$HOME", str(pathlib.Path.home())))
    if "run_on_install" in install_configs:
        if sys.platform != "win32":
            os.system(f"sh {pathlib.Path.home() / pathlib.Path("Fluid") / pathlib.Path(repo)}/{install_configs["run_on_install"]}")
    if "run_on_install_win32" in install_configs:
        if sys.platform == "win32":
            os.system(f"{pathlib.Path.home() / pathlib.Path("Fluid") / pathlib.Path(repo)}/{install_configs["run_on_install_win32"]}")
    if "official" in install_configs:
        if not install_configs["official"]:
            if input("You are installing non verified package. Install? [y/n]") != "y":
                raise SystemExit
