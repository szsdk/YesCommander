import os

from .. import xdg


def init_config_folder() -> None:
    if not xdg.config_path.exists():
        xdg.config_path.mkdir(parents=True, exist_ok=True)
    config_file = xdg.config_path / "yc_rc.py"

    if not config_file.exists():
        import pkg_resources

        init_cfg_path = pkg_resources.resource_filename(
            "yescommander", "example/yc_rc.py"
        )
        print(f"==== initalize {str(config_file)} ====")
        with open(init_cfg_path, "r") as fp:
            print(fp.read())
        os.system(f"cp {init_cfg_path} {config_file}")
    exit()
