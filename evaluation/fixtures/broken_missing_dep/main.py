import requests
import yaml

config = yaml.safe_load("name: demo\nversion: 1")
print(f"{config['name']} v{config['version']}, requests {requests.__version__}")
