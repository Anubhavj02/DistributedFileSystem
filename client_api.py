import base64
import json
from tempfile import SpooledTemporaryFile
import requests
from Crypto.Cipher import AES
from pymongo import MongoClient
import time
import server_messages_list


# mongo setup stuff
mongo_server = "localhost"
mongo_port = "27017"
connect_string = "mongodb://" + mongo_server + ":" + mongo_port
connection = MongoClient(connect_string)
distributed_file_system_db = connection.distributedfilesystem
LOCK_SERVER_ADDR = "http://127.0.0.1:8004/lock_server/"


def create_user(user_id, password_16char, public_key_32char):
    """function to create user
                        Args:
                            user_id: user login ID
                            password_16char: 16 character password
                            public_key_32char: 32 character Public Key
    """
    headers = {'Content-type': 'application/json'}
    payload = {'user_id': user_id
        , 'user_password': password_16char
        , 'public_key': public_key_32char}
    response = requests.post("http://localhost:5000/user/createUser", data=json.dumps(payload), headers=headers)
    return response.text


def login_user(user_id, password):
    """function to enable login user
                        Args:
                            user_id: user login ID
                            password: 16 character password
    """
    headers = {'Content-type': 'application/json'}
    payload = {'user_id': user_id
        , 'user_password': password}
    response = requests.post("http://localhost:5000/user/authenticateUser", data=json.dumps(payload), headers=headers)
    return response.text


def upload_file(file_directory, file_path, login_request, user_id):
    """function to upload file and user must be logged in
                            Args:
                                file_directory: directory of the file to be stored
                                file_path: path of the file
                                login_request: login response containing unique Authenticated Ticket
                                user_id: Unique ID of the user
    """

    data, headers, server_host, server_port = process_request_header(file_directory, file_path, login_request, user_id)

    request = requests.post("http://" + server_host + ":" + server_port + "/fileOperations/uploadFile", data=data,
                            headers=headers)
    return request.text


def download_file(file_directory, file_path, login_request, user_id):
    """function to download file and user must be logged in
                            Args:
                                file_directory: directory of the file to be stored
                                file_path: path of the file
                                login_request: login response containing unique Authenticated Ticket
                                user_id: Unique ID of the user
    """

    data, headers, server_host, server_port = process_request_header(file_directory, file_path, login_request, user_id)

    request = requests.post("http://" + server_host + ":" + server_port + "/fileOperations/downloadFile",
                            headers=headers)
    file = open("../" + request.text)

    return file


def read_file(file_directory, file_path, login_request, user_id):
    """function to read file and user must be logged in
                                Args:
                                    file_directory: directory of the file to be stored
                                    file_path: path of the file
                                    login_request: login response containing unique Authenticated Ticket
                                    user_id: Unique ID of the user
    """

    data, headers, server_host, server_port = process_request_header(file_directory, file_path, login_request, user_id)

    request = requests.post("http://" + server_host + ":" + server_port + "/fileOperations/readFile",
                            headers=headers)
    return request.text


def process_request_header(file_directory, file_path, login_request, user_id, write = False, file_data =''):
    """function to process the request header and user must be logged in
                                    Args:
                                        file_directory: directory of the file to be stored
                                        file_path: path of the file
                                        login_request: login response containing unique Authenticated Ticket
                                        user_id: Unique ID of the user
                                        write: Flag whether we are writing data or not
                                        file_data: file data to be written
    """

    # Fetch the details of the user from DB
    user_details = distributed_file_system_db.dfs_users.find_one({'user_id': user_id})
    # Get the public key of the user
    user_public_key = user_details['public_key']
    hashed_public_key = AES.new(user_public_key, AES.MODE_ECB)
    # Get the log in ticket
    encoded_user_ticket = json.loads(login_request)["user_ticket"]
    decoded_user_ticket = hashed_public_key.decrypt(base64.b64decode(encoded_user_ticket))
    data = json.loads(decoded_user_ticket.strip())

    user_session_id = data["session_id"]
    server_host = data["server_host"]
    server_port = data["server_port"]
    access_key = data["access_key"]
    # Encrypt the session ID and hash it
    hashed_session_id = AES.new(user_session_id, AES.MODE_ECB)

    # Encrypted file directory
    encrypted_dir = base64.b64encode(
        hashed_session_id.encrypt(file_directory + b" " * (AES.block_size - len(file_directory) % AES.block_size)))
    # Encrypted file file name
    encrypted_file_name = base64.b64encode(
        hashed_session_id.encrypt(file_path + b" " * (AES.block_size - len(file_path) % AES.block_size)))

    data = open(file_path, 'rb').read()
    # if write is true change the headers
    if write:
        headers = {'access_key': access_key
            , 'file_directory': encrypted_dir
            , 'file_name': encrypted_file_name
            , 'file_data': file_data}
    else:
        headers = {'access_key': access_key
        , 'file_directory': encrypted_dir
        , 'file_name': encrypted_file_name}

    return data, headers, server_host, server_port

# This class manages all the temporary file operations
class FileManagement(SpooledTemporaryFile):
    def __init__(self, filename, directory, user_id, file_data=''):
        self.filename = filename
        self.directory = directory
        self.user_id = user_id
        SpooledTemporaryFile.__init__(self, 100000, 'write')
        self.check_lock_server()
        response = requests.post(LOCK_SERVER_ADDR+"lockFile", json={'file_path': filename, 'lock_file': True, 'user_id':self.user_id})

    def check_lock_server(self):
        """function to check the status of the file server, ping the server until it becomes unlocked
        """
        file_locked = True
        while file_locked:
            response = requests.get(LOCK_SERVER_ADDR+"getLockStatus", {'file_path': self.filename, 'user_id': self.user_id})
            if response.json()['file_locked']:
                file_locked = True
                time.sleep(5)
            else:
                file_locked = False
        return

    def close_file(self):
        """function to close the file and release the lock so that the other user can edit
        """
        SpooledTemporaryFile.flush(self)
        response = requests.post(LOCK_SERVER_ADDR, json={'file_path': self.filename, 'lock_file': False, 'user_id': self.user_id})
        print response

    def write_file_contents(self, login_request, user_id, data):
        data, headers, server_host, server_port = process_request_header(self.directory, self.filename, login_request,
                                                                         user_id, True, data)
        response = requests.post("http://" + server_host + ":" + server_port + "/fileOperations/writeFile",
                                headers=headers)
        if response.status_code != 200:
            raise Exception(server_messages_list.ERROR_WRITE)

