import argparse

from flask import Flask

from flask import request
from flask import jsonify
import server_messages_list

app = Flask(__name__)


@app.route('/lock_server/getLockStatus', methods=['GET'])
def get_file_lock_status():
    """function to get the status of the file lock
    """
    file_path = request.args.get('file_path')
    client_id = request.args.get('user_id')
    file_locked = lock_server.check_file_locked(file_path, client_id)
    response_data = {'file_locked': file_locked}
    response = jsonify(response_data)
    response.status_code = 200
    return response


@app.route('/lock_server/lockFile', methods=['POST'])
def put_file_lock():
    """function to put the lock on the file
    """
    if request.headers['Content-Type'] == 'application/json':
        data = request.json
        file_path = data['file_path']
        lock_file = data['lock_file']
        user_id = data['user_id']
        # If file not locked, lock it
        if lock_file:
            file_status = lock_server.put_file_lock(file_path, user_id)
        # Unlock it if locked
        else:
            file_status = lock_server.file_unlocker(file_path, user_id)
        response_data = {'file_lock_status': file_status}
        response = jsonify(response_data)
        response.status_code = 200
        return response


# Class for handling all the lock operations
class LockServer:

    def __init__(self, server_host, server_port):
        self.host_addr = "http://"+server_host+":"+str(server_port)+"/"
        self.host = server_host
        self.port = server_port
        self.locked_files_list = {}

    def put_file_lock(self, file_path, user_id):
        """function to put lock on the file
                    Args:
                        file_path: path of the file to be locked
                        user_id: user Id working on locked file
        """
        # If file in locked in list put the details
        if file_path not in self.locked_files_list:
            self.locked_files_list[file_path] = [user_id]
            return True
        # If file is in the list append the user to the file
        elif user_id not in self.locked_files_list[file_path]:
            self.locked_files_list[file_path].append(user_id)
            return True
        else:
            return False

    def file_unlocker(self, file_path, user_id):
        """function to unlock the file
                        Args:
                            file_path: path of the file to be locked
                            user_id: user Id working on locked file
        """
        # If file not locked file list raise error
        if file_path not in self.locked_files_list:
            raise Exception(server_messages_list.FILE_UNLOCKING)
        # Delete the user from the list and delete the file from lock list
        elif self.locked_files_list[file_path] != [] and user_id == self.locked_files_list[file_path][0]:
            del self.locked_files_list[file_path][0]
            return True
        else:
            return True

    def check_file_locked(self, path, user_id):
        """function to unlock the file
                        Args:
                            path: path of the file to be locked
                            user_id: user Id working on locked file
        """
        # Iterate through all the locked file list
        for file_path, value in self.locked_files_list.items():
            if file_path == path and self.locked_files_list[file_path] != []:
                if self.locked_files_list[file_path][0] == user_id:
                    return False
                else:
                    return True
        return False


if __name__ == '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument(
        '--server_host',
        type=str,
        default='127.0.0.1',
        help='IP of server where it is hosted'
    )
    args_parser.add_argument(
        '--server_port',
        type=int,
        default=8004,
        help='port of the server'
    )
    ARGS, unparsed = args_parser.parse_known_args()
    lock_server = LockServer(ARGS.server_host, ARGS.server_port)
    app.run(host=ARGS.server_host, port=ARGS.server_port)