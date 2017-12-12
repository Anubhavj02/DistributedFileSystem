import base64
import hashlib

from Crypto.Cipher import AES
from flask import Flask
from flask import jsonify
from flask import request
from pymongo import MongoClient
import string
import random

mongodb_server = "localhost"
mongodb_port = "27017"
connection = MongoClient("mongodb://" + mongodb_server + ":" + mongodb_port)
distributed_file_system_db = connection.distributedfilesystem
distributed_file_system_db.dfs_users.drop()
distributed_file_system_db.dfs_servers.drop()
distributed_file_system_db.dfs_directories.drop()
distributed_file_system_db.dfs_files.drop()
distributed_file_system_db.dfs_transactions.drop()
hash_key = hashlib.md5()

app = Flask(__name__)


@app.route('/user/create', methods=['POST'])
def user_creation():
    print "-- Creating a new user --"
    request_data = request.get_json(force=True)
    user_id = request_data.get('user_id')
    user_password = request_data.get('user_password')
    public_key = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(32))
    encrypted_user_password = base64.b64encode(AES.new(public_key, AES.MODE_ECB).encrypt(user_password))
    session_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(29))

    distributed_file_system_db.dfs_users.insert(
        {"user_id": user_id
            , "session_id": session_id
            , "public_key": public_key
            , "pwd": encrypted_user_password}
    )
    return jsonify({"Message": "User Created",
                    "User ID": user_id})


if __name__ == '__main__':
    app.run()
