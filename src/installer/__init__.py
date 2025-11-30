import json
import os

import requests, pathlib, zipfile, shutil

def install(repository: str, author: str = "Fluid-Packages", path: pathlib.Path = pathlib.Path.home() / pathlib.Path("Fluid"), allowed_author: str = "Fluid-Packages", api: str = "https://api.github.com/repos/{}"):
    request_url = api_url = f"https://api.github.com/repos/{author}/{repository}"
    response = requests.get(request_url)
    response.raise_for_status()
    data = response.json(); branch = data.get("default_branch", "main")
    request_url = f"https://github.com/{author}/{repository}/archive/refs/heads/{branch}.zip"
    response = requests.get(request_url, stream=True)
    response.raise_for_status()
    zip_path = path / f"{repository}.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with open(zip_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(path)
    extracted = path / f"{repository}-{branch}"
    final_dir = path / repository
    if extracted.exists():
        if final_dir.exists():
            shutil.rmtree(final_dir)
        extracted.rename(final_dir)
    config = dict()
    if (final_dir/".fluid").exists():
        if "package.json" in os.listdir(final_dir / ".fluid"):
            with open(str(final_dir/".fluid") + "/package.json") as configs:
                config = json.load(configs)
    zip_path.unlink()
    if author != allowed_author: config["official"] = False
    return config

def uninstall(repository: str, path: pathlib.Path = pathlib.Path.home() / pathlib.Path("Fluid")):
    shutil.rmtree(path / repository)
