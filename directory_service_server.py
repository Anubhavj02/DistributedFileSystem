import base64  # Used for encoding and decoding
import datetime
import hashlib  # For hashing
from Crypto.Cipher import AES  # Encryption of the keys using AES method
from diskcache import Cache  # Cache package of python
from flask import Flask
from flask import jsonify  # To convert string to JSON
from flask import request
from pymongo import MongoClient  # Package to interact with MongoDB
import server_messages_list  # File containing description of every error
import flask
import server_transaction_service  # Server Transaction Packages
import threading  # To implement threads

app = Flask(__name__)

# 32 Character authentication for the server
AUTH_KEY = 'ASGS328BHREH3923H312J1DSJ1223321'

# Establishing connection to MongoDB
connection = MongoClient("mongodb://" + "localhost" + ":" + "27017")
distributed_file_system_db = connection.distributedfilesystem
SERVER_HOSTNAME = None
SERVER_PORT = None

#  Path to store all cached files
file_cache = Cache('/tmp/cache')
transaction_server = server_transaction_service.TransactionServer()


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


def async_file_upload(file, directory, headers):
    """function to decrypt string on basis of Decryption key
        Args:
            file: file to be uploaded
            directory: directory of the file
            headers: request headers
    """
    print "\n--- Asynchronously Uploading File ---\n"
    transaction_server.async_upload(file, directory, headers)


@app.route('/fileOperations/uploadFile', methods=['POST'])
def file_upload():
    """function to upload files to the server, it accepts filename, directory, access_key in the header
    """
    print "\n-- Upload File Requested By the User --\n"

    file_details, file_directory, req_headers = file_upload_transaction()

    # Upload the user's file to the server
    transaction_thread = threading.Thread(target=async_file_upload, args=(file_details['dir_identifier'], file_directory['dir_identifier'], req_headers),
                           kwargs={})
    transaction_thread.start()

    # Sending response back to client
    return jsonify({'success': True,
                    'Message': server_messages_list.UPLOAD_SUCCESS})


@app.route('/fileOperations/checkUploadFile', methods=['POST'])
def check_file_upload():
    """function to check the status of the uploaded file
    """
    print "\n-- Upload File Requested --\n"

    try:
        # Start the file upload transaction
        file_upload_transaction()
    except Exception:
        return jsonify({'success': False,
                        'Message': server_messages_list.UPLOAD_ERROR})

    return jsonify({'success': True,
                    'Message': server_messages_list.UPLOAD_SUCCESS})


def file_upload_transaction():
    """function to find the file and directory if they exist otherwise create them
    """
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

        # Insert the directory details in th DB
        distributed_file_system_db.dfs_directories.insert({"dir_name": req_decrypted_directory
                                                              , "dir_identifier": hash_key.hexdigest()
                                                              , "dir_server": get_server_object()["dir_identifier"]})
        file_directory = distributed_file_system_db.dfs_directories.find_one(
            {"dir_name": req_decrypted_directory, "dir_identifier": hash_key.hexdigest(),
             "dir_server": get_server_object()["dir_identifier"]})
    else:
        print "\n-- Requested Directory exists, fetch the directory details --\n"

        # As ths directory exist fetch its detail
        file_directory = distributed_file_system_db.dfs_directories.find_one(
            {"dir_name": req_decrypted_directory, "dir_identifier": hash_key.hexdigest(),
             "dir_server": get_server_object()["dir_identifier"]})

    # Check if the files exists in the server
    if not distributed_file_system_db.dfs_files.find_one(
            {"file_name": req_decrypted_filename, "directory": file_directory['dir_identifier'],
             "dir_server": get_server_object()["dir_identifier"]}):
        print "\n-- Requested File does not exist, create the file and insert the file details in DB --\n"

        # Creating a unique hash key for each file
        hash_key = hashlib.md5()
        hash_key.update(file_directory['dir_identifier'] + "/" + file_directory['dir_name'] + "/" + get_server_object()[
            'dir_identifier'])
        distributed_file_system_db.dfs_files.insert({"file_name": req_decrypted_filename
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
            {"file_name": req_decrypted_filename, "directory": file_directory['dir_identifier'],
             "dir_server": get_server_object()["dir_identifier"]})
    else:
        print "\n-- File exists, fetch the details of the file --\n"
        file_details = distributed_file_system_db.dfs_files.find_one(
            {"file_name": req_decrypted_filename, "directory": file_directory['dir_identifier'],
             "dir_server": get_server_object()["dir_identifier"]})

    return file_details, file_directory, req_headers


@app.route('/fileOperations/downloadFile', methods=['POST'])
def file_download():
    """function to download the uploaded files from the server
    """
    print "\n-- DOWNLOAD FILE REQUEST FROM THE USER --\n"
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

    # First find the file directory
    file_directory = distributed_file_system_db.dfs_directories.find_one(
        {"dir_name": req_decrypted_directory, "dir_identifier": hash_key.hexdigest(),
         "dir_server": get_server_object()["dir_identifier"]})

    # If directory does not exist return error
    if not file_directory:
        return jsonify({"success": False,
                        "Message": server_messages_list.DIRECTORY_ERROR})

    # Now find the details of the files from the DB
    file_details = distributed_file_system_db.dfs_files.find_one(
        {"file_name": req_decrypted_filename, "directory": file_directory['dir_identifier'],
         "dir_server": get_server_object()["dir_identifier"]})

    # If file does not exists return error
    if not file_details:
        server_transaction_service.insert_transaction(file_details["file_name"] + file_directory['dir_name'], get_server_object(), "ERROR")
        return jsonify({"success": False})

    server_transaction_service.insert_transaction(file_details["file_name"] + file_directory['dir_name'],
                                                  get_server_object(), "COMPLETED")
    return file_details['dir_identifier']


@app.route('/fileOperations/readFile', methods=['POST'])
def file_read():
    """function to read file from the server
    """
    print "\n-- DOWNLOAD FILE REQUEST FROM THE USER --\n"
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

    # First find the file directory
    file_directory = distributed_file_system_db.dfs_directories.find_one(
        {"dir_name": req_decrypted_directory, "dir_identifier": hash_key.hexdigest(),
         "dir_server": get_server_object()["dir_identifier"]})

    # If directory does not exist return error
    if not file_directory:
        return jsonify({"success": False,
                        "Message": server_messages_list.DIRECTORY_ERROR})

    # Now find the details of the files from the DB
    file_details = distributed_file_system_db.dfs_files.find_one(
        {"file_name": req_decrypted_filename, "directory": file_directory['dir_identifier'],
         "dir_server": get_server_object()["dir_identifier"]})

    # If file does not exists return error
    if not file_details:
        server_transaction_service.insert_transaction(file_details["file_name"] + file_directory['dir_name'],
                                                      get_server_object(), "ERROR")
        return jsonify({"success": False})

    # Perform caching
    cache_hash = file_details['dir_identifier'] + "/" + file_directory['dir_identifier'] + "/" + get_server_object()[
        "dir_identifier"]
    server_transaction_service.insert_transaction(file_details["file_name"] + file_directory['dir_name'],
                                                  get_server_object(), "COMPLETED")
    if file_cache.get(cache_hash):
        return file_cache.get(cache_hash)
    else:
        return flask.send_file(file_details['dir_identifier'])


@app.route('/fileOperations/writeFile', methods=['POST'])
def file_write():
    """function to write file from the server
    """
    print "\n-- DOWNLOAD FILE REQUEST FROM THE USER --\n"
    req_headers = request.headers
    # Get the details from the header
    req_encrypted_filename = req_headers['file_name']
    req_encrypted_directory = req_headers['file_directory']
    req_access_key = req_headers['access_key']
    file_data = req_headers['file_data']
    user_session_id = decrypt_string(AUTH_KEY, req_access_key).strip()
    req_decrypted_directory = decrypt_string(user_session_id, req_encrypted_directory)
    req_decrypted_filename = decrypt_string(user_session_id, req_encrypted_filename)

    hash_key = hashlib.md5()
    hash_key.update(req_decrypted_directory)

    # First find the file directory
    file_directory = distributed_file_system_db.dfs_directories.find_one(
        {"dir_name": req_decrypted_directory, "dir_identifier": hash_key.hexdigest(),
         "dir_server": get_server_object()["dir_identifier"]})

    # If directory does not exist return error
    if not file_directory:
        return jsonify({"success": False,
                        "Message": server_messages_list.DIRECTORY_ERROR})

    # Now find the details of the files from the DB
    file_details = distributed_file_system_db.dfs_files.find_one(
        {"file_name": req_decrypted_filename, "directory": file_directory['dir_identifier'],
         "dir_server": get_server_object()["dir_identifier"]})

    # If file does not exists return error
    if not file_details:
        return jsonify({"success": False})

    with open("./"+file_details['dir_identifier'], "a") as file:
        file.write(file_data)

    return jsonify({"success": False,
                    "message": server_messages_list.WRITE_SUCCESS})


if __name__ == '__main__':
    with app.app_context():
        # Traverse through the available servers
        for dfs_server in distributed_file_system_db.dfs_servers.find():
            # Check if the server is active and if not active use it
            if not dfs_server['active']:
                # Setting active true in the server
                dfs_server['active'] = True
                SERVER_PORT = dfs_server['server_port']
                SERVER_HOSTNAME = dfs_server['server_host']
                distributed_file_system_db.dfs_servers.update({'dir_identifier': dfs_server['dir_identifier']},
                                                              dfs_server, upsert=True)
                # run the directory service server on this server
                app.run(host=dfs_server['server_host'], port=dfs_server['server_port'])
