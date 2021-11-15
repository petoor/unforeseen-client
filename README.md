### All scripts needs to be ran from the root folder ###

# Optional - Rename the hostname to reflect what device it is.
hostnamectl set-hostname DEVICE_NETWORK_NAME-DEVICE_NAME

## Create the SETUP.yml file.
python initial_setup/create_default_setup.py

## Create basic index.html
python initial_setup/create_index_html.py

## Start the cronjobs
python system/start_cronjobs.py
get crontab info with cat /var/log/syslog
# Start stream 
# python analysis/hello-world.py
