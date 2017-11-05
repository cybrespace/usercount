#!/usr/bin/python3

from six.moves import urllib
from datetime import datetime
from subprocess import call
from mastodon import Mastodon
import time
import threading
import csv
import os
import json
import time
import signal
import sys
import os.path        # For checking whether secrets file exists
import requests       # For doing the web stuff, dummy!

from fullwidth import fullwidth

###############################################################################
# INITIALISATION
###############################################################################

do_upload = True
# Run without uploading, if specified
if '--no-upload' in sys.argv:
    do_upload = False

# Check mastostats.csv exists, if not, create it
if not os.path.isfile("mastostats.csv"):    
        print("mastostats.csv does not exist, creating it...")

        # Create CSV header row
        with open("mastostats.csv", "w") as myfile:
            myfile.write("timestamp,usercount,instancecount\n")
        myfile.close()

if not os.path.isfile("cybrestats.csv"):    
        print("cybrestats.csv does not exist, creating it...")

        # Create CSV header row
        with open("cybrestats.csv", "w") as myfile:
            myfile.write("timestamp,usercount,pingscount\n")
        myfile.close()

# Returns the parameter from the specified file
def get_parameter( parameter, file_path ):
    # Check if secrets file exists
    if not os.path.isfile(file_path):    
        print("File %s not found, exiting."%file_path)
        sys.exit(0)

    # Find parameter in file
    with open( file_path ) as f:
        for line in f:
            if line.startswith( parameter ):
                return line.replace(parameter + ":", "").strip()

    # Cannot find parameter, exit
    print(file_path + "  Missing parameter %s "%parameter)
    sys.exit(0)

# Load secrets from secrets file
secrets_filepath = "secrets/secrets.txt"
uc_client_id     = get_parameter("uc_client_id",     secrets_filepath)
uc_client_secret = get_parameter("uc_client_secret", secrets_filepath)
uc_access_token  = get_parameter("uc_access_token",  secrets_filepath)

# Load configuration from config file
config_filepath = "config.txt"
mastodon_hostname = get_parameter("mastodon_hostname", config_filepath) # E.g., mastodon.social

# Initialise Mastodon API
mastodon = Mastodon(
    client_id = uc_client_id,
    client_secret = uc_client_secret,
    access_token = uc_access_token,
    api_base_url = 'https://' + mastodon_hostname,
)

# Initialise access headers
headers={ 'Authorization': 'Bearer %s'%uc_access_token }


###############################################################################
# GET THE DATA
###############################################################################

# Get current timestamp
ts = int(time.time())

page = requests.get('https://instances.social/instances.json')

instances = json.loads(page.content.decode("utf-8", "ignore"))

user_count = 0
instance_count = 0
for instance in instances:
    if not "users" in instance: continue
    user_count += instance["users"]
    if instance["up"] == True:
        instance_count += 1

print("Number of users: %s " % user_count)
print("Number of instances: %s " % instance_count)

cybrepage = requests.get('https://' + mastodon_hostname + '/about/more').content.decode("utf-8", "ignore")

def get_between(s, substring1, substring2):
    return s[(s.index(substring1)+len(substring1)):s.index(substring2)]

# Remove newlines to make our life easier
pagecontent = cybrepage.replace("\n", "")

# Get the number of users, removing commas
current_id = int( get_between(pagecontent, "Home to</span><strong>", "</strong><span>users").replace(",", ""))

# Get the number of toots, removing commas
num_toots = int (get_between(pagecontent, "Who authored</span><strong>", "</strong><span>pings").replace(",", ""))

# Get the number of toots, removing commas
num_cnxns = int (get_between(pagecontent, "Connected to</span><strong>", "</strong><span>other instances").replace(",", ""))

print("Number of cybreusers: %s "% current_id)
print("Number of pings: %s "% num_toots )
print("Number of connections: %s "% num_cnxns )


###############################################################################
# LOG THE DATA
###############################################################################

# Append to CSV file
with open("mastostats.csv", "a") as myfile:
    myfile.write(str(ts) + "," + str(user_count) + "," + str(instance_count) + "\n")

with open("cybrestats.csv", "a") as myfile:
    myfile.write(str(ts) + "," + str(current_id) + "," + str(num_toots) + "," + str(num_cnxns) + "\n")


###############################################################################
# WORK OUT THE TOOT TEXT
###############################################################################

# Load CSV file
with open('mastostats.csv') as f:
    usercount_dict = [{k: int(v) for k, v in row.items()}
        for row in csv.DictReader(f, skipinitialspace=True)]

with open('cybrestats.csv') as f:
    cybrecount_dict = [{k: int(v) for k, v in row.items()}
        for row in csv.DictReader(f, skipinitialspace=True)]

# Returns the timestamp,usercount pair which is closest to the specified timestamp
def find_closest_timestamp( input_dict, seek_timestamp ):
    a = []
    for item in input_dict:
        a.append( item['timestamp'] )
    return input_dict[ min(range(len(a)), key=lambda i: abs(a[i]-seek_timestamp)) ]


# Calculate difference in times

cybre_users = (-1,-1)
cybre_cnxns = (-1,-1)
cybre_pings = (-1,-1)

ntwrk_users = (-1,-1)
ntwrk_insts = (-1,-1)

one_hour = 60 * 60
one_day  = one_hour * 24
one_week = one_hour * 168

# Daily change
if len(usercount_dict) > 24:
    one_day_ago_ts = ts - one_day
    one_day_ago_ntwrk = find_closest_timestamp( usercount_dict, one_day_ago_ts )
    one_day_ago_cybre = find_closest_timestamp( cybrecount_dict, one_day_ago_ts )
    cybre_users = (current_id, current_id - one_day_ago_cybre['usercount'])
    cybre_cnxns = (num_cnxns, num_cnxns - one_day_ago_cybre['connectioncount'])
    cybre_pings = (num_toots, num_toots - one_day_ago_cybre['pingscount'])

    ntwrk_users = (user_count, user_count - one_day_ago_ntwrk['usercount'])
    ntwrk_insts = (instance_count, instance_count - one_day_ago_ntwrk['instancecount'])


###############################################################################
# CREATE AND UPLOAD THE CHART
###############################################################################

# Generate chart
call(["gnuplot", "generate_all.gnuplot"])
call(["gnuplot", "generate_cybre.gnuplot"])


if do_upload:
    # Upload chart


    file_to_upload = 'graph.png'

    print("Uploading %s..."%file_to_upload)
    media_dict0 = mastodon.media_post(file_to_upload)

    print("Uploaded file, returned:")
    print(str(media_dict0))



    file_to_upload = 'graph_cybre.png'

    print("Uploading %s..."%file_to_upload)
    media_dict = mastodon.media_post(file_to_upload)

    print("Uploaded file, returned:")
    print(str(media_dict))


    ###############################################################################
    # T  O  O  T !
    ###############################################################################

    def rightpad(s, n):
        while (len(s) < n): s += " "
        return fullwidth(s)

    colwidth = max(len(str(cybre_users[0])) + len(str(cybre_users[1])) + 8,
                   len(str(cybre_cnxns[0])) + len(str(cybre_cnxns[1])) + 13,
                   len(str(cybre_pings[0])) + len(str(cybre_pings[1])) + 8,
                   17)

    toot_text =  "NETWORK STATS\n"
    toot_text +=  "users: {:,} ({:+} today)\n".format(*ntwrk_users)
    toot_text +=  "instances: {:,} ({:+} today)\n".format(*ntwrk_insts)

    toot_text += "\nCYBRESPACE STATS\n"
    toot_text += "users: {:,} ({:+} today)\n".format(*cybre_users)
    toot_text += "connections: {:,} ({:+} today)\n".format(*cybre_cnxns)
    toot_text += "pings: {:,} ({:+} today)\n".format(*cybre_pings)


    print("Tooting..." )
    print(toot_text)

    mastodon.status_post(toot_text, in_reply_to_id=None, media_ids=[media_dict0, media_dict])

    print("Successfully tooted!")
else:
    print("--no-upload specified, so not uploading anything")
