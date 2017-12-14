import base64  # Used for encoding and decoding

from Crypto.Cipher import AES  # Encryption of the keys using AES method
from flask import Flask  # Rest Service package
from flask import jsonify  # Convert strings to JSON to send response
from flask import request
from pymongo import MongoClient  # Package to interact with MongoDB
import string  # All utilities functions related to string
import random  # generate random keys
import json  # JSON package
import server_messages_list  # File containing description of every error
import hashlib

# Mongo DB Connection details
mongodb_server = "localhost"
mongodb_port = "27017"

# Establishing connection with MongoDB
connection = MongoClient("mongodb://" + mongodb_server + ":" + mongodb_port)

# Connecting to MongoDB connection named 'distributedfilesystem'
distributed_file_system_db = connection.distributedfilesystem

# Drop all the previous tables
distributed_file_system_db.dfs_users.drop()
distributed_file_system_db.dfs_servers.drop()
distributed_file_system_db.dfs_directories.drop()
distributed_file_system_db.dfs_files.drop()
distributed_file_system_db.dfs_transactions.drop()

hashed_key = hashlib.md5()

# Adding the details of Master and worker sever in the DB
hashed_key.update("localhost" + ":" + "9001")
distributed_file_system_db.dfs_servers.insert(
    {"dir_identifier": hashed_key.hexdigest(), "server_host": "localhost", "server_port": "9001", "master": True,
     "active": False})

hashed_key.update("localhost" + ":" + "9002")
distributed_file_system_db.dfs_servers.insert(
    {"dir_identifier": hashed_key.hexdigest(), "server_host": "localhost", "server_port": "9002", "master": False,
     "active": False})

hashed_key.update("localhost" + ":" + "9003")
distributed_file_system_db.dfs_servers.insert(
    {"dir_identifier": hashed_key.hexdigest(), "server_host": "localhost", "server_port": "9003", "master": False,
     "active": False})

app = Flask(__name__)

# 32 Character unique key for the server
AUTH_KEY = "ASGS328BHREH3923H312J1DSJ1223321"


@app.route('/user/createUser', methods=['POST'])
def user_creation():
    """function to create users for the distributed file system, it will accept a JSON string in request with userId
        and password
    """
    print "-- Creating a new user --"

    # Getting data from the JSON request
    request_data = request.get_json(force=True)
    user_id = request_data.get('user_id')
    user_password = request_data.get('user_password')
    public_key = request_data.get('public_key')

    # Generating random public key for every user that requests

    # Encrypting user password using public key and AES algorithm
    encrypted_user_password = base64.b64encode(AES.new(public_key, AES.MODE_ECB).encrypt(user_password))

    # Generating random session for the current user login
    session_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(29))

    # Inserting the user details in the Mongo DB
    distributed_file_system_db.dfs_users.insert(
        {"user_id": user_id, "session_id": session_id, "public_key": public_key,
         "user_password": encrypted_user_password}
    )

    # Sending response back to client
    return jsonify({"success": True,
                    "Message": server_messages_list.USER_CREATE_SUCCESS,
                    "User ID": user_id})


@app.route('/user/authenticateUser', methods=['POST'])
def user_authentication():
    """function to authenticate users for the distributed file system, it will accept a JSON string in request with userId
            and password
    """
    data = request.get_json(force=True)
    user_password = data.get('user_password')
    user_id = data.get('user_id')
    print "Authenticate Request from the user with userID:" + user_id
    user_details = distributed_file_system_db.dfs_users.find_one({'user_id': user_id})
    encrypted_password = user_details['user_password']
    public_key = user_details['public_key']
    decrypted_user_password = AES.new(public_key, AES.MODE_ECB).decrypt(base64.b64decode(encrypted_password)).strip()

    if decrypted_user_password == user_password:
        session_id = ''.join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(32))
        user_details['session_id'] = session_id
        if distributed_file_system_db.dfs_users.update({'user_id': user_id}, user_details, upsert=True):
            curr_user = user_details
        else:
            return jsonify({'success': False,
                            'error': "Error: " + server_messages_list.DB_UPDATE_FAILURE})
    else:
        return jsonify({'success': False,
                        'error': "Error: " + server_messages_list.PASSWORD_MISMATCH})
    if curr_user:
        session_key_hashed = curr_user['session_id'] + b" " * (
            AES.block_size - len(curr_user['session_id']) % AES.block_size)
        encoded_hashed_session_key = base64.b64encode(AES.new(AUTH_KEY, AES.MODE_ECB).encrypt(session_key_hashed))

        user_ticket = json.dumps(
            {'session_id': curr_user['session_id'], 'server_host': "localhost", 'server_port': "9001",
             'access_key': encoded_hashed_session_key})
        user_ticket_hash_format = user_ticket + b" " * (AES.block_size - len(user_ticket) % AES.block_size)
        encode_hash_ticket = base64.b64encode(
            AES.new(curr_user['public_key'], AES.MODE_ECB).encrypt(user_ticket_hash_format))
        print "\nUser Authorized Successful\n"
        return jsonify({'success': True,
                        'user_ticket': encode_hash_ticket,
                        "Message": server_messages_list.USER_AUTH})
    else:
        return jsonify({'success': False,
                        'error': "Error: " + server_messages_list.USER_NOT_FOUND})


if __name__ == '__main__':
    app.run()
