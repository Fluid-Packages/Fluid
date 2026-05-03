import requests
import zipfile
import pathlib
import os, json
import sys, time
import shutil

BASE_DIR = pathlib.Path.home()/"Fluid"
BASE_REPO = "https://raw.githubusercontent.com/Fluid-Packages/base-repo/refs/heads/main/repo.json"
ACTIONS = ("install", "uninstall", "show", "fetch", "run")

def help():
    print(f"Usage: {sys.argv[0]} <action> [packages]\n\n\
Examples:\
\n\t{sys.argv[0]} install vscode       | Install package\
\n\t{sys.argv[0]} uninstall python     | Uninstall package\
\n\t{sys.argv[0]} show                 | Show installed packages\
\n\t{sys.argv[0]} fetch                | Upgrade repositories\
\n\t{sys.argv[0]} run libresprite      | Run package binaries\
\n\t{sys.argv[0]} packages             | Show all packages\
\n\t{len(sys.argv[0])*" "} |-> OR pkgs | repos | repositories")
    sys.exit()

def parse_argv(argv: list[str]):
    argv = argv[1:]
    if len(argv) == 0:
        help()
        return
    
    action = argv[0]

    if action in ("show","repos","repositories","pkgs","packages"):
        return action, []
    elif action == "fetch":
        fetch()
        sys.exit(0)
        return
    elif len(argv) < 2 or action not in ACTIONS:
        help()
        return
    
    packages = argv[1:]

    return action, packages

def fetch():
    if "repositories.json" not in os.listdir(BASE_DIR):
        with open(BASE_DIR/"repositories.json", "w") as f:
            json.dump({"repos":[BASE_REPO]}, f, indent=4)
    if "packages.json" not in os.listdir(BASE_DIR):
        with open(BASE_DIR/"packages.json", "w") as f:
            json.dump({"packages":dict()}, f, indent=4)

    with open(BASE_DIR/"repositories.json") as f:
        repos = json.load(f)
    
    print("Starting...")

    packages = dict()
    for repo in repos["repos"]:
        s = time.time()
        print(f"\tFetching {repo}")
        r = requests.get(repo)
        print(f"\tFetched in {time.time()-s:.2f} seconds")
        r.raise_for_status()
        data = json.loads(r.text)
        for pkg in data["packages"]:
            packages[pkg] = data["packages"][pkg]
            print(f"\t\t- {pkg}")
    
    with open(BASE_DIR/"packages.json", "w") as f:
        repos = json.dump({"packages" : packages}, f)
        print("Success!")

def get_packages():
    with open(BASE_DIR/"packages.json") as f:
        pkgs = json.load(f)["packages"]
    return pkgs

def _install_file(link: str, name: str, saveas: str):
    response = requests.get(link, stream=True)
    response.raise_for_status()
    path = BASE_DIR/"packages"/name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir()

    with open(f"{path}/{saveas}", 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return path

def install(link: str, name: str, saveas: str | None = None):
    if saveas == None: saveas = name
    if not link.endswith(".zip"):
        return _install_file(link, name, saveas)

    response = requests.get(link, stream=True)
    response.raise_for_status()
    zip_path = BASE_DIR/"packages"/name
    if zip_path.exists():
        shutil.rmtree(zip_path)
    zip_path.mkdir()
    with open(f"{zip_path}/{name}.zip", 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    with zipfile.ZipFile(f"{zip_path}/{name}.zip", 'r') as zip_ref:
        members = zip_ref.namelist()
        roots = set()
        for m in members:
            parts = m.split('/')
            if parts[0]:
                roots.add(parts[0])

        if len(roots) == 1:
            root_folder = list(roots)[0]

            for m in members:
                stripped = m[len(root_folder):].lstrip('/')

                if not stripped:
                    continue

                target_path = os.path.join(zip_path, stripped)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                with zip_ref.open(m) as src, open(target_path, 'wb') as dst:
                    dst.write(src.read())
        else:
            zip_ref.extractall(zip_path)
    return zip_path

def main():
    action, packages = parse_argv(sys.argv)

    if not os.path.exists(BASE_DIR):
        os.mkdir(str(BASE_DIR))
    if not os.path.exists(BASE_DIR/"packages"):
        os.mkdir(str(BASE_DIR/"packages"))

    match action:
        case "install":
            print("Re-fetching all repositories...")
            fetch()

            for package in packages:
                if package in get_packages():
                    pkg = get_packages()[package]
                    print(f"\nFound {package}")
                    print("Installing...")
                    try:
                        if os.name == "nt" and pkg["links"]["nt"] != None: install(pkg["links"]["nt"], package, pkg["links"]["save-as"]["nt"])
                        elif sys.platform == "darwin" and pkg["links"]["darwin"] != None: install(pkg["links"]["darwin"], package, pkg["links"]["save-as"]["darwin"])
                        elif os.name == "posix" and pkg["links"]["posix"] != None: install(pkg["links"]["posix"], package, pkg["links"]["save-as"]["posix"])
                        else: install(pkg["src"], package)

                        if os.name == "nt" and pkg["setup"]["nt"] != None: 
                            dir = os.getcwd()
                            os.chdir(BASE_DIR/"packages"/package)
                            for command in pkg["setup"]["nt"]:
                                os.system(command)
                            os.chdir(dir)
                        elif sys.platform == "darwin" and pkg["setup"]["darwin"] != None: 
                            dir = os.getcwd()
                            os.chdir(BASE_DIR/"packages"/package)
                            for command in pkg["setup"]["darwin"]:
                                os.system(command)
                            os.chdir(dir)
                        elif os.name == "posix" and pkg["setup"]["posix"] != None: 
                            dir = os.getcwd()
                            os.chdir(BASE_DIR/"packages"/package)
                            for command in pkg["setup"]["posix"]:
                                os.system(command)
                            os.chdir(dir)
                    except KeyboardInterrupt:
                        print("Operation cancelled by user.")
                        return
                    except Exception as e:
                        print(f"Unknown error occured. {e}")
                        continue
                    print("Success!")
                else:
                    print(f"\nCant find {package} in repositories")
                    continue
        case "run":
            print("Re-fetching all repositories...")
            fetch()
            if len(packages) > 1:
                help()
                return
            pkg = packages[0]
            pkgs = os.listdir(BASE_DIR/"packages")
            if not (pkg in pkgs and pkg in list(get_packages())):
                print(f"\nCant find {pkg} in repositories")
                return
            pkgs = get_packages()
            pkg = pkgs[packages[0]]
            try:
                if os.name == "nt" and pkg["run"]["nt"] != None: 
                    dir = os.getcwd()
                    os.chdir(BASE_DIR/"packages"/packages[0])
                    for command in pkg["run"]["nt"]:
                        os.system(command)
                    os.chdir(dir)
                elif sys.platform == "darwin" and pkg["run"]["darwin"] != None: 
                    dir = os.getcwd()
                    os.chdir(BASE_DIR/"packages"/packages[0])
                    for command in pkg["run"]["darwin"]:
                        os.system(command)
                    os.chdir(dir)
                elif os.name == "posix" and pkg["run"]["posix"] != None: 
                    dir = os.getcwd()
                    os.chdir(BASE_DIR/"packages"/packages[0])
                    for command in pkg["run"]["posix"]:
                        os.system(command)
                    os.chdir(dir)
            except KeyboardInterrupt:
                print("Operation cancelled by user.")
                return
            except Exception as e:
                print(f"Unknown error occured. {e}")
                return

        case "uninstall":
            if not os.path.exists(BASE_DIR/"packages"):
                os.mkdir(BASE_DIR/"packages")
            
            for package in packages:
                if package not in os.listdir(BASE_DIR/"packages"):
                    print(f"\nCant find {package}")
                    print("Exiting...", end="\n\n")
                    return
                shutil.rmtree(BASE_DIR/"packages"/package)
                print(f"\nSuccesfully removed {package}")
        case "show":
            if not os.path.exists(BASE_DIR/"packages"):
                os.mkdir(BASE_DIR/"packages")

            print("\nInstalled packages:")

            if len(os.listdir(BASE_DIR/"packages")) == 0:
                print("\t| no packages |", end="\n\n")
                return
            for package in os.listdir(BASE_DIR/"packages"):
                print(f"\t- {package}")
        case "repos" | "packages" | "repositories" | "pkgs":
            if "repositories.json" not in os.listdir(BASE_DIR):
                with open(BASE_DIR/"repositories.json", "w") as f:
                    json.dump({"repos":[BASE_REPO]}, f, indent=4)
            if "packages.json" not in os.listdir(BASE_DIR):
                with open(BASE_DIR/"packages.json", "w") as f:
                    json.dump({"packages":dict()}, f, indent=4)

            print("\nAvaliable packages:")
            pkgs = get_packages()
            for pkg in list(pkgs):
                print(f" - {pkg}")
            print("\nFrom repositories:")
            for repo in json.load(open(BASE_DIR/"repositories.json"))["repos"]:
                print(f" - {repo}")
    print()

if __name__ == "__main__":
    try:    
        main()
    except Exception as e:
        print(f"An error occured. {e}")