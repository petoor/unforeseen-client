import yaml

def setup_loader(file="SETUP.yml") -> dict:
    with open(file, "r") as stream:
        settings = yaml.safe_load(stream)
    return settings
