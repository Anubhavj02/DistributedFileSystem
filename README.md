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
* **Distributed Transparent File Access(client_api.py):** 
<br>For this part of the project, a client API was made so that the user/client can easily access the distributed file system with simple interface of command as shown in the file "testing_client/client.py". A client can use the API/client libarary to do the following things:
	* Create a new user of the system
	* Login to the system
	* Download file
	* Upload file
	* Read file
	* Write File

* Security Service(authentication_server.py): 
<br> A new user can be can be created by the userID, 16char password(its multiple as it is used in encryption with 32 char key), and a 32 char unique public key. Password is encrypted by the public key using AES encryption and then stored in DB
<br><br>
When the user login with his user ID and password and if it is correct, user is assigned with Unique Ticket to do further operations. When user requests for a login his passowrd is decrypted against the public key stored corresponding to the user in the DB and matched with the stored password in DB, if correct user is assigned a unique random session ID and Ticket which is composed of Session ID, server details and access_key of the server.

  The user needs the Ticket details to interact with system as it contains server details and session ID used for further encryption of files and directories.
  
  
* Directory Service(directory_service_server.py):
<br>
The above file is responsible handling all the directory and file handling operations. It maps the human readable file names and directory names to a proper and unique identifier; and vice versa. All operations require user to be logged in and have the ticket with ssession Id and server details

This enables the following operations:<br>
* Upload a file: it takes user's file and the input directory and the unique ticket where the user wants to store the file. It checks whether the directory exists or otherwise creates it and same for the file creates it if doesn't
exit

* Download File/ Read: By the file name and directory, and session ID, file details are fetched. And if file exists in cache it is read from there otherwise from the directory

* Write File: By file name, directory and session Id, a dummy temporary file is create where user can write contents and the file locked until user closes it, then the lock is realsed and file changes are now commited from temp to original and cache is updated

* Caching(server_transaction_service.py):
Caching is used for faster access. File once uploaded are stored in cache and updated regularly upon write.
So once user request for file read or download it is directly accessed using the python Diskcache package 


* Transaction(server_transaction_service.py):
<br>
All the transaction are stored and mapped into the DB and which server carried out this operation.
The dfs_transaction db store all the details. When the files are uploaded, downloaded, or read all the transaction are stored with "COMPLETED" and "ERROR" message. 
	Functions are implemented to get the total success and total failure count that can be used when the application is further scaled
    

* Lock (lock_server.py):
<br>Locking is used to avoid simultaneous write operation into a same file. When a client is writing into the file, that file is locked and no other user can write into it until the user closes it, once it is closed the lock is released; other users can use it now. It is used to avoid deadlock and concurrent access 
