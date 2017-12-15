#!/usr/bin/env bash
# Script file for executing the chat server on the machine and accept the first command line argument as port number

echo "Name: Anubhav Jain, Student Id: 17310876"

echo "Distributed File System"

echo "Running the authentication Server"
python authentication_server.py --sever_host $1 --sever_port $3

echo "Running the directory Server"
python directory_service_server.py

echo "Running the lock Server"
python lock_server.py --sever_host $2 --sever_port $4