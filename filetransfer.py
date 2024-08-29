import socket
import threading
import os

# Function to get the users IP address
def get_user_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a public DNS server to determine local IP address
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1' #safe local IP, limited functionality
    finally:
        s.close()
    return ip

# Function to handle receiving files, is run on a seperate thread initiated in main
def receive_files(server_socket):
    while True:
        try:
            conn, addr = server_socket.accept()
            print(f"\nConnection from {addr}")

            # Receive the filename length first (4 bytes)
            name_length = int.from_bytes(conn.recv(4), 'big')
            
            # Receive the actual filename
            file_name = conn.recv(name_length).decode()
            print(f"Receiving file: {file_name}")

            with open(file_name, 'wb') as file:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    file.write(data)

            print(f"File '{file_name}' received successfully\n")
            conn.close()

        except Exception as e:
            print(f"Error receiving file: {e}")

 # Function to send files
def send_file(filename, target_host, target_port):
    try:
        # make sure file exists otherwise return error
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File '{filename}' not found.")
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((target_host, target_port))
        
        # Send the filename length first (4 bytes) this makes sure that the file receiver receives the file with the proper name and file extension
        file_name_bytes = os.path.basename(filename).encode()
        client_socket.sendall(len(file_name_bytes).to_bytes(4, 'big'))
        
        # Send the real filename
        client_socket.sendall(file_name_bytes)
        
        # Send file content in chunks of 1024 bytes
        with open(filename, 'rb') as file:
            for data in iter(lambda: file.read(1024), b''):
                client_socket.sendall(data)

        print(f"File '{filename}' sent successfully\n")
        client_socket.close()

        #ensures program doesnt crash if conenction is unsuccessful
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ConnectionRefusedError:
        print(f"Error: Unable to connect to {target_host}:{target_port}. Please check the IP address and port number.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    # Setup for receiving files
    host = get_user_ip()  # Get local IP address
    receive_port = 5001
    user_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    user_socket.bind((host, receive_port))
    user_socket.listen(1)
    
    print(f"Your IP address is: {host}")
    print(f"Listening for incoming connections on port {receive_port}\n")

    # Start a thread to handle incoming connections
    receive_thread = threading.Thread(target=receive_files, args=(user_socket,))
    receive_thread.daemon = True  #thread is marked as daemon so it will close with the main fdnction
    receive_thread.start()

    # Send files to another user
    while True:
        try:
            target_host = input("Enter the IP address of the recipient: ")
            target_port = int(input("Enter the port number of the recipient: "))
            filename = input("Enter the path to the file to send: ")
            send_file(filename, target_host, target_port)

        except ValueError:
            print("Error: Invalid input for port number. Please enter a valid integer.")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
