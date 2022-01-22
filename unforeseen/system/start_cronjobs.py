import os
import sys

from crontab import CronTab

from unforeseen.config import setup_loader

setup = setup_loader()

root = setup.get("device").get("root")  # type: ignore
cron = CronTab(user=True)
cron.remove_all()

# Sync and remove
sync_and_remove = cron.new(
    command=f"cd {root} && python -OO system/scripts/sync_remove.py >> {root}/storage/logging/sync_and_remove.log"
)
sync_and_remove.minute.on(0)

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
