from pymongo import MongoClient  # Package to interact with the MongoDB client
from flask import Flask
import threading
from diskcache import Cache
import requests
import hashlib
from flask_pymongo import PyMongo

# Thread lock to hold the process until a thread has completed its job
lock = threading.Lock()
app = Flask(__name__)
mongo = PyMongo(app)
connection = MongoClient("mongodb://" + "localhost" + ":" + "27017")
distributed_file_system_db = connection.distributedfilesystem
AUTH_KEY = "ASGS328BHREH3923H312J1DSJ1223321"
SERVER_RESPONSE_CODE = 200

# Set the cache instance
cache = Cache('/tmp/cache')


def get_server_object(server_host, server_port):
    """function to get the current server details from the database
            Args:
                server_host: hostname of the server
                server_port: port on which this server is running
    """
    with app.app_context():
        return distributed_file_system_db.dfs_servers.find_one({"server_host": server_host, "server_port": server_port})


# This class comprises of the methods to transact the sever to upload/ download
class TransactionServer:

    def async_upload(self, file_info, directory, headers):
        """function to upload the file aysnchronously
                    Args:
                        file_info: file information to be uploaded
                        directory: port on which this server is running
                        headers: request headers
        """
        with app.app_context():

            # Traverse through the available server and check which server has the data
            dfs_servers = distributed_file_system_db.dfs_servers.find()
            for dfs_server in dfs_servers:
                server_host = dfs_server["server_host"]
                server_port = dfs_server["server_port"]
                # Building the hash code to access the content of the cache
                hashed_cache = file_info + "/" + directory + "/" + dfs_server['dir_identifier']
                # Fetch the data from the cache
                cache_data = cache.get(hashed_cache)

                # If there is no data for the particular server, move to other
                if cache_data is None:
                    continue

                if server_host is None and server_port is None:
                    continue

                # Open the file input stream and write the data
                with open(file_info, "wb") as fopen:
                    fopen.write(cache_data)

                headers = {'access_key': headers['access_key'],
                           'file_directory': headers['file_directory'],
                           'file_name': headers['file_name']}

                # Checking if the file is uploaded or not
                check_upload_file_request = requests.post("http://" + server_host + ":" + server_port + "/fileOperations/checkUploadFile", data=cache_data, headers=headers)
                # Check the file upload status
                if check_upload_file_request.status_code == SERVER_RESPONSE_CODE:
                    print "File Uploaded Successfully"
                    insert_transaction(file_info + directory, dfs_server, "COMPLETED")
                else:
                    print "File Upload Problem"
                    insert_transaction(file_info + directory, dfs_server, "ERROR")


def insert_transaction(file_name, server_details, response_status):
    hash_key = hashlib.md5()
    hash_key.update(file_name)
    transaction = distributed_file_system_db.dfs_transactions.find_one({"trans_id": hash_key.hexdigest()})
    if transaction:
        transaction["logs"] = response_status
    else:
        distributed_file_system_db.dfs_transactions.insert(
            {"trans_id": hash_key.hexdigest(), "logs": response_status, "server-id": server_details['dir_identifier']})


def get_transaction(name):
    hash_key = hashlib.md5()
    hash_key.update(name)
    return distributed_file_system_db.dfs_transactions.find_one({"trans_id": hash_key.hexdigest()})


def get_success_count():
    count = 0
    for transaction in distributed_file_system_db.dfs_transactions.find():
        if transaction['logs'] == "COMPLETED":
            count += 1
    return count


def get_failure_count():
    count = 0
    for transaction in distributed_file_system_db.dfs_transactions.find():
        if transaction['logs'] == "ERROR":
            count += 1
    return count


