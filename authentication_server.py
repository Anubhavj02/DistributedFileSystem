import base64  # Used for encoding and decoding

from Crypto.Cipher import AES  # Encryption of the keys using AES method
from flask import Flask  # Rest Service package
from flask import jsonify  # Convert strings to JSON to send response
from flask import request
from pymongo import MongoClient  # Package to interact with MongoDB
import string  # All utilities functions related to string
import random  # generate random keys
import json   # JSON package
import server_error_list  # File containing description of every error


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

app = Flask(__name__)
# Generating a random authentication number for the server
AUTH_KEY = ''.join(random.choice(string.digits + string.ascii_lowercase) for _ in range(32))


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

    # Generating random public key for every user that requests
    public_key = ''.join(
        random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(32))

    # Encrypting user password using public key and AES algorithm
    encrypted_user_password = base64.b64encode(AES.new(public_key, AES.MODE_ECB).encrypt(user_password))

    # Generating random session for the current user login
    session_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(29))

    # Inserting the user details in the Mongo DB
    distributed_file_system_db.dfs_users.insert(
        {"user_id": user_id
            , "session_id": session_id
            , "public_key": public_key
            , "user_password": encrypted_user_password}
    )

    # Sending response back to client
    return jsonify({"Message": "User Created",
                    "User ID": user_id})


if __name__ == '__main__':
    app.run()
