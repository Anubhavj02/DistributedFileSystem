import base64  # Used for encoding and decoding
import datetime
import hashlib
from Crypto.Cipher import AES  # Encryption of the keys using AES method
from diskcache import Cache  # Cache package of python
from flask import Flask
from flask import jsonify
from flask import request
from pymongo import MongoClient  # Package to interact with MongoDB
import server_messages_list  # File containing description of every error

app = Flask(__name__)

# 32 Character authentication for the server
AUTH_KEY = 'ASGS328BHREH3923H312J1DSJ1223321'
mongo_server = "localhost"
mongo_port = "27017"

# Establishing connection to MongoDB
connection = MongoClient("mongodb://" + mongo_server + ":" + mongo_port)
distributed_file_system_db = connection.distributedfilesystem
SERVER_HOSTNAME = None
SERVER_PORT = None

#  Path to store all cached files
file_cache = Cache('/tmp/cache')


def decrypt_string(decryption_key, hashed_string):
    """function to decrypt string on basis of Decryption key
        Args:
            decryption_key: the key to perform decryption
            hashed_string: string in hash string format that need to be decrypted
    """
    decrypted_string = AES.new(decryption_key, AES.MODE_ECB).decrypt(base64.b64decode(hashed_string))
    return decrypted_string


def get_server_object():
    """get the server instance from the mongoDB
    """
    with app.app_context():
        return distributed_file_system_db.dfs_servers.find_one(
            {"server_host": SERVER_HOSTNAME, "server_port": SERVER_PORT})


@app.route('/fileOperations/uploadFile', methods=['POST'])
def file_upload():
    """function to upload files to the server, it accepts filename, directory, access_key in the header
    """
    print "\n-- Upload File Requested --\n"
    req_data = request.get_data()
    req_headers = request.headers
    # Get the details from the header
    req_encrypted_filename = req_headers['file_name']
    req_encrypted_directory = req_headers['file_directory']
    req_access_key = req_headers['access_key']
    user_session_id = decrypt_string(AUTH_KEY, req_access_key).strip()
    req_decrypted_directory = decrypt_string(user_session_id, req_encrypted_directory)
    req_decrypted_filename = decrypt_string(user_session_id, req_encrypted_filename)
    hash_key = hashlib.md5()
    hash_key.update(req_decrypted_directory)

    # Check if the directory exits or not
    if not distributed_file_system_db.dfs_directories.find_one(
            {"dir_name": req_decrypted_directory, "dir_identifier": hash_key.hexdigest(),
             "dir_server": get_server_object()["dir_identifier"]}):
        print "\n-- Requested Directory does not exist, create the directory --\n"
        hash_key = hashlib.md5()
        hash_key.update(req_decrypted_directory)
        distributed_file_system_db.dfs_directories.insert({"dir_name": req_decrypted_directory
                                                              , "dir_identifier": hash_key.hexdigest()
                                                              , "dir_server": get_server_object()["dir_identifier"]})
        file_directory = distributed_file_system_db.dfs_directories.find_one(
            {"dir_name": req_decrypted_directory, "dir_identifier": hash_key.hexdigest(),
             "dir_server": get_server_object()["dir_identifier"]})
    else:
        print "\n-- Requested Directory exists, fetch the directory details --\n"
        file_directory = distributed_file_system_db.dfs_directories.find_one(
            {"dir_name": req_decrypted_directory, "dir_identifier": hash_key.hexdigest(),
             "dir_server": get_server_object()["dir_identifier"]})

    # Check if the files exists in the server
    if not distributed_file_system_db.dfs_files.find_one(
            {"dir_name": req_decrypted_filename, "directory": file_directory['dir_identifier'],
             "dir_server": get_server_object()["dir_identifier"]}):
        print "\n-- Requested File does not exist, create the file and insert the file details in DB --\n"
        hash_key = hashlib.md5()
        hash_key.update(file_directory['dir_identifier'] + "/" + file_directory['dir_name'] + "/" + get_server_object()[
            'dir_identifier'])
        distributed_file_system_db.dfs_files.insert({"dir_name": req_decrypted_filename
                                                    , "directory": file_directory['dir_identifier']
                                                    , "dir_server": get_server_object()["dir_identifier"]
                                                    , "dir_identifier": hash_key.hexdigest()
                                                    , "time_updated": datetime.datetime.utcnow()})

        file_details = distributed_file_system_db.dfs_files.find_one({'dir_identifier': hash_key.hexdigest()})
        # Put the details of the file in the cache
        cache_hash = file_details['dir_identifier'] + "/" + file_directory['dir_identifier'] + "/" + \
                     get_server_object()["dir_identifier"]
        file_cache.set(cache_hash, req_data)

        # Open the file and write contents into it
        with open(file_details['dir_identifier'], "wb") as fopen:
            fopen.write(
                file_details['dir_identifier'] + "/" + file_directory['dir_identifier'] + "/" + get_server_object()[
                    "dir_identifier"])

        file_details = distributed_file_system_db.dfs_files.find_one(
            {"dir_name": req_decrypted_filename, "directory": file_directory['dir_identifier'],
             "dir_server": get_server_object()["dir_identifier"]})
    else:
        print "\n-- File exists, fetch the details of the file --\n"
        file_details = distributed_file_system_db.dfs_files.find_one(
            {"dir_name": req_decrypted_filename, "directory": file_directory['dir_identifier'],
             "dir_server": get_server_object()["dir_identifier"]})
    return jsonify({'success': True,
                    'Message': server_messages_list.UPLOAD_SUCCESS})


if __name__ == '__main__':
    with app.app_context():
        # Finding the details of all the server present in DB and fetching their details
        for curr_server in distributed_file_system_db.dfs_servers.find():
            # Check if the server is active and if not active use it
            if not curr_server['active']:
                # Setting active true in the server
                curr_server['active'] = True
                SERVER_PORT = curr_server['server_port']
                SERVER_HOSTNAME = curr_server['server_host']
                distributed_file_system_db.dfs_servers.update({'dir_identifier': curr_server['dir_identifier']},
                                                              curr_server, upsert=True)
                # Running the directory service on the server
                app.run(host=curr_server['server_host'], port=curr_server['server_port'])
