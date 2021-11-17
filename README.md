### All scripts needs to be ran from the root folder ###

# Optional - Rename the hostname to reflect what device it is.
hostnamectl set-hostname DEVICE_NETWORK_NAME-DEVICE_NAME

## Install unforeseen as a package
pip install -e .
# We add the -e flag to be in in editable mode.
# That means we can add models and functions to the package without rebuilding.
# However we do need to restart the session to acces the new functions.

## Create the SETUP.yml file.
python initial_setup/create_default_setup.py

## Create basic index.html
python initial_setup/create_index_html.py

## Start the cronjobs
python system/start_cronjobs.py

# (Optional) Start stream 
# python analysis/hello-world.py
