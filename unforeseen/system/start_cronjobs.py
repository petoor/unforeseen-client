import os, sys
from crontab import CronTab
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unforeseen.config import setup_loader
setup = setup_loader()

root = setup.get("device").get("root")
cron = CronTab(user=True)
cron.remove_all()

# Sync and remove
sync_and_remove = cron.new(command=f'cd {root} && python3 system/scripts/sync_remove.py > storage/logging/sync_and_remove.log')
sync_and_remove.minute.on(0)

# Backup settings
backup = cron.new(command=f'cd {root} && python3 system/scripts/backup_settings.py > storage/logging/backup.log')
backup.minute.on(0)
backup.hour.on(0)

# Start http (hls) server if machine goes down
port = setup.get("server").get("port")
server = cron.new(command=f'cd {root} && python3 -m http.server {port} > storage/logging/server.log')
server.every_reboot()

# Start analysis
script = setup.get("model").get("script")
pipeline = setup.get("model").get("pipeline")
camera = "/dev/video0"
use_db = 1
use_gpio = 1
analysis = cron.new(command=f'cd {root} && python3 analysis/{script} --pipeline {pipeline} --camera {camera} --use_gpio {use_gpio} --use_db {use_db} > storage/logging/analysis.log')
analysis.every_reboot()
cron.write()
