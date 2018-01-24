#!/usr/bin/python

import paramiko
import threading
import os.path
import subprocess
import time
import sys
import re
import yaml

class Device:

    def __init__(self, name, mgmt_ip, router_id, role):
        self.name = name
        self.mgmt_ip = mgmt_ip
        self.router_id = router_id
        self.role = role

    def set_ping_status(self,result):
        self.ping_status = result

    def get_ping_status(self):
        return self.ping_status 


## Ping test to check connectivity.

def ping_test(ip_address):
    try:
        result = subprocess.check_output("ping -c 1 {} ".format( ip_address), shell=True)
    
    except Exception, e:
        return False
    
    return True


##Sub to run command using ssh protocol.

def run_command_ssh(channel_name, command):
    response = str()
    channel_data = []
    channel = channel_name
    channel.send(command + "\n")
    time.sleep(1) 
    while True:
        if channel.recv_ready():
            response = channel.recv(9999)
            channel_data.append(response)
            if response.endswith("#"):
                break
    complete_response = "".join(channel_data)
    print "    Working on command: " + command
    return complete_response


## SSH to the device and collect data.

def ssh_2_device(device_name, device_ip, credentials, commands):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    uid = credentials[0].strip()
    pwd = credentials[1].strip()
    client.connect(device_ip, username = uid, password = pwd)
    channel = client.invoke_shell()
    channel.send("term le 0\n")
    log_file_name = "log_" + device_name + "_" + time.strftime("%Y%m%d_%H%M%S") 
    print "Working on device: " + device_name 
    with open(log_file_name, "w") as log:
        for command in commands:
            response = run_command_ssh(channel, command)
            log.write(response)
    channel.close()
    client.close()
    return 
        

## Read datafile and create inventory and other entries. 

with open('datafile.yml', "r+") as f:
    dataMap = yaml.safe_load(f)
    inventory = []
    log_dir = dataMap.get("log_dir")
    credentials = []
    credentials.append(dataMap.get("userid"))
    credentials.append(dataMap.get("password"))
    for item in dataMap.get("devices"):

            device_name = item.get("name")
            mgmt_ip     = item.get("mgmt_ip")
            router_id   = item.get("router_id")
            role        = item.get("role")
            
            inventory.append((Device(device_name, mgmt_ip, router_id, role)))
    
    master_commands_list = dataMap.get("commands")
'''    for key in commands.keys():
        print commands[key][0]
        print commands[key][1]
'''
print "\n"
print "###################"
print "Check connectivity."
print "###################"

for device_entry in inventory:
    mgmt_ip = device_entry.mgmt_ip
    if ping_test(mgmt_ip) is True:
        print device_entry.name +" is reachable."
        device_entry.set_ping_status(True)
    else:
        print device_entry.name + " is not reachable."
        device_entry.set_ping_status(False)

print "\n"
print "#####################################"
print "Collect data from accessible devices."
print "#####################################"

for device_entry in inventory:
    ping_status = device_entry.get_ping_status()
    if ping_status is True:
        role = device_entry.role
        role_commands = master_commands_list[role]
        ssh_2_device(device_entry.name, device_entry.mgmt_ip, credentials, role_commands)

