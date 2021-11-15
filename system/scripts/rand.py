import random
from datetime import datetime
import os, sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import logging
from unforeseen-client.config import setup_loader
setup = setup_loader()
now = datetime.now()
num = random.randint(1,101)
with open("rand.txt",'a') as f:
    f.write(f"The random number is {num} at time {now} \n")
    f.write(f'{setup.get("server").get("port")}')
    logging.info("Wrote and entry log")
    print("Wrote and entry print")
