import client_api

# Creating a new user
print (client_api.create_user("2", "123456789sdcdsdd", "hdavjh232hg428ywd908ehbjd823sdc2"))

# Login using the new user
login_response = client_api.login_user("2", "123456789sdcdsdd")
print (login_response)

# Uploading a file
print (client_api.upload_file("/demoloc/files", "../demo_files/demo_file1.txt", login_response, "2"))

# Downloading a file
print (client_api.download_file("/demoloc/files", "../demo_files/demo_file1.txt", login_response, "2"))

# Reading a file
print (client_api.read_file("/demoloc/files", "../demo_files/demo_file1.txt", login_response, "2"))


file1 = client_api.FileManagement("../demo_files/demo_file1.txt", "/demoloc/files", "write")
file1.write_file_contents(login_response, "2", "demo test")
file1.close_file()