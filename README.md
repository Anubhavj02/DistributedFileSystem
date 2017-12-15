# Distributed File Management System

This is distributed file system where multiple users can manage their file and can perform file related operations. This system is implemented using Flask Rest Package and with Mongo DB as the database for storing all the information.

>Name: Anubhav Jain
<br>TCD Student ID: 17310876

Following things are implemented in this project:
* Distributed Transparent File Access
* Security Service
* Directory Service
* Caching
* Transactions
* Lock Service

## Dependencies Required
* Python 2.7
* Flask 0.12.2 - Rest service package
* MongoDB - Database to store the details
* diskcache 2.9.0 - for implementing caching
* PyMongo 3.5.1 - To interact with the MomgoDB
* Pycrypto 2.6.1 - to enable encryption and decryption

## Starting the servers and running the code
1. **Run the shell script to run all the servers**
    ```sh
    sh start.sh {authentication_server_ip} {lock_server_ip} {authentication_server_port} {lock_server_port}
    ```
    where
    * authentication_server_ip - ip where all the authentication server will run
    * lock_server_ip - ip where lock server will run
    * authentication_port - port where authentication server will run
    * lock_server_port - port where lock server will run

    This will run the following servers
    * Authentication server - Carry out user creation and authentication
    * Lock Server - To implement locking
    * Directory Server - Implementing directory service and caching

2. **Or Run Directly by Python: you can run directly with python commands each server in the order specified below:**
* Run the authentication server
  ```sh
  python authentication_server.py --server_host {server_ip} --server_port {server_port}
  ```
  Both options are optional
  Default values are:
  * IP (localhost): 127.0.0.1
  * Port: 5000
  
* Run the Directory server
  ```sh
  python directory_service_server.py
  ```
  This server will pick the ports and IP from the predefined ports and server details stored in MongoDB.
  They are the predefined worker server details stored in DB
  

* Run the Lock Server server
  ```sh
  python lock_server.py --server_host {server_ip} --server_port {server_port}
  ```
  Both options are optional
  Default values are:
    * IP (localhost): 127.0.0.1
    * Port: 8004

## Testing the Distributed File System
To test the system and all the functionalities run the servers as mentioned in the above steps.
and then in the terminal run the following command
```sh
  python testing_clients/client.py
  ```
  
### Output of the following command if all servers are in running state
```sh
/System/Library/Frameworks/Python.framework/Versions/2.7/bin/python2.7 /var/root/PycharmProjects/DistributedFileSystem/testing_clients/client.py
{
  "Message": "User Created Successfully", 
  "User ID": "2", 
  "success": true
}

{
  "Message": "User Authorized Successfully", 
  "success": true, 
  "user_ticket": "F7HjR2bfVhWAE/Cd4+2eie57wj/f0txWW5/+GJdN2CRdaHm1hHkL0J1+/y/rPmSS/7pZOGGQC6gsxk+fAg/+N19xLnidINaGcGYCST+GCMHTmr0ksgun04lLQUCz6YQISG9pAXKkAPuPxRxwkmZVOMhu+MOlXI9jK4KcdogHCi2y6QdghDGrL2NQsxbzabk2UEDM1pSz5FSyqVTVYjhq+JYyJlYtC1u6H0bdmssw5sE2+bOknDvBQU8uKKg4cJAw"
}

{
  "Message": "File uploaded successfully", 
  "success": true
}

<open file u'../8a092e1e9e9b8fe82887528fb612fb77', mode 'r' at 0x10648a6f0>
This is the first demo file
Process finished with exit code 0
```

## Evaluating and understanding the system
* Distributed Transparent File Access: 
