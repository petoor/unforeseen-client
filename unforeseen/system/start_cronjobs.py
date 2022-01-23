import os
import sys

from crontab import CronTab
from numpy import delete

from unforeseen.config import setup_loader

setup = setup_loader()

root = setup.get("device").get("root")  # type: ignore
cron = CronTab(user=True)
cron.remove_all()

# Sync files
nas = setup.get("storage").get("NAS")
password = nas.get("password")  # type: ignore
server_user = nas.get("user")  # type: ignore
server_ip = nas.get("ip")  # type: ignore
protocol = nas.get("protocol")  # type: ignore
server_path = nas.get("path")  # type: ignore
device_name = setup.get("device").get("name")  # type: ignore

sync = cron.new(
    command=f"cd {root} && sshpass -p {password} {protocol} -a storage/ {server_user}@{server_ip}:{server_path}/data/{device_name} >> {root}/storage/logging/sync_files.log"
)
sync.minute.on(0)

# Delete files
delete_files = cron.new(
    command=f"cd {root} && python -OO system/scripts/delete_files.py >> {root}/storage/logging/delete_files.log"
)
delete_files.minute.on(0)

# Backup settings
backup = cron.new(command=f"cd {root} && python -OO system/scripts/backup_settings.py >> {root}/storage/logging/backup.log")
backup.minute.on(0)
backup.hour.on(0)

# Start http (hls) server if machine goes down
hls_sink_port = setup.get("server").get("hls_sink_port")  # type: ignore
server = cron.new(command=f"cd {root} && python -m http.server {hls_sink_port} >> {root}/storage/logging/server.log")
server.every_reboot()

# Start analysis
script = setup.get("model").get("script")  # type: ignore
pipeline = setup.get("model").get("pipeline")  # type: ignore
camera = setup.get("model").get("camera")  # type: ignore
use_db = setup.get("model").get("use_db")  # type: ignore
use_gpio = setup.get("model").get("use_gpio")  # type: ignore
use_model = setup.get("model").get("use_model")  # type: ignore
analysis = cron.new(command=f"cd {root} && python -OO {script} --pipeline {pipeline} --camera {camera} --use_gpio {use_gpio} --use_db {use_db} --use_model {use_model} >> {root}/storage/logging/analysis.log")  # type: ignore # noqa
analysis.every_reboot()
cron.write()
