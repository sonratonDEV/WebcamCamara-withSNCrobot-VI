import cv2
import os
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from pyModbusTCP.client import ModbusClient

screen_fol = 'screen'
i = 1
prev_state = None
frame = None
state = None
line = '0'
registers = None
image_matrix = [[1, 10, 11, 20, 21, 30, 31, 40],
                [2, 9, 12, 19, 22, 29, 32, 39],
                [3, 8, 13, 18, 23, 28, 33, 38],
                [4, 7, 14, 17, 24, 27, 34, 37],
                [5, 6, 15, 16, 25, 26, 35, 36]]

# Create a GUI window
root = tk.Tk()
root.geometry('1200x550')
root.title("Camera and Serial Monitor")

# Create a frame to contain the components
frame1 = ttk.Frame(root)
frame1.grid(row=0, column=0, rowspan=6)

frame2 = ttk.Frame(root)
frame2.grid(row=0, column=1)

# Create a frame for IP connection within frame1
ip_frame = ttk.Frame(frame1)
ip_frame.grid(row=3, column=0, columnspan=2)

# Function to set the folder path
def set_folder_path():
    folder_path = folder_name_var.get()
    if folder_path:
        global screen_fol, i
        screen_fol = folder_path
        i = 1
        print(f"Folder path set to: {screen_fol}")

        # Clear the existing labels
        for widget in frame2.winfo_children():
            widget.destroy()

        # Create the folder if it doesn't exist
        if not os.path.exists(screen_fol):
            os.makedirs(screen_fol)
            print(f"Folder created: {screen_fol}")

# Create a frame for folder input and refresh button within frame1
folder_frame = ttk.Frame(frame1)
folder_frame.grid(row=4, column=0, columnspan=2)

# Entry widget to input the folder name
folder_entry_label = ttk.Label(folder_frame, text="Enter Folder Name:")
folder_entry_label.grid(row=0, column=0)
folder_name_var = tk.StringVar()
folder_entry = ttk.Entry(folder_frame, textvariable=folder_name_var)
folder_entry.grid(row=0, column=1)

# Button to set the folder path
set_folder_button = ttk.Button(folder_frame, text="Set Folder Path", command=set_folder_path)
set_folder_button.grid(row=0, column=2)
    
# Function to display the captured screenshots in the grid
def display_screenshots():
    # global image_matrix
    for row, image_row in enumerate(image_matrix):
        for col, image_num in enumerate(image_row):
            image_path = os.path.join(screen_fol, f'{screen_fol}_{image_num}.png')
            if os.path.exists(image_path):
                img = Image.open(image_path)
                img = img.resize((100, 100), Image.LANCZOS)  # Resize the image with anti-aliasing
                img = ImageTk.PhotoImage(img)  # Convert to a format that tkinter can display

                # Create a label to display the image
                label = ttk.Label(frame2, image=img)
                label.grid(row=row, column=col)
                label.image = img  # Keep a reference to the image to prevent it from being garbage collectedee

# Function to update serial connection state
def update_ipstate():
    if modbusClient is not None:
        ip_connect_label.config(text=" IP: Connected", foreground="green")
    else:
        ip_connect_label.config(text=" IP: Not Connected", foreground="red")

# Function to update camera connection state
def update_camera_state():
    if cap.isOpened():
        camera_label.config(text="Camera: Connected", foreground="green")
    else:
        camera_label.config(text="Camera: Not Connected", foreground="red")

# Function to start the camera connection
def start_camera():
    global cap
    cap = cv2.VideoCapture(1)  # Open the camera
    if cap.isOpened():
        update_camera_state()

    # Use the entered folder name or default to 'screen' if not provided
    folder_name = folder_name_var.get() or 'screen'
    folder_path = os.path.join(os.getcwd(), folder_name)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    camera_thread = threading.Thread(target=lambda: camera_thread_function(folder_path))
    camera_thread.start()

# Function to stop the camera connection
def stop_camera():
    global cap
    if cap.isOpened():
        cap.release()
        update_camera_state()

def start_ipconnect():
    global ip_address, port, modbusClient

    ip_stopped.clear()
    ip_address = ip_var.get()
    port = port_var.get()
    unit_id = 1
    modbusClient = ModbusClient(host=ip_address, port=port, unit_id=unit_id, auto_open=True)

    if modbusClient is not None:
        update_ipstate()
    ip_thread = threading.Thread(target=ip_thread_function)
    ip_thread.start()

# Function to stop the IP connection
def stop_ipconnect():
    global modbusClient
    try:
        if modbusClient is not None:
            modbusClient = None
            update_ipstate()
            ip_stopped.set()  # Set the event to stop the ip_thread_function
    except:
        pass

#Cameara Components
# Button to start the camera connection within frame1
start_camera_button = ttk.Button(frame1, text="Start Camera", command=start_camera)
start_camera_button.grid(row=0, column=0)

# Button to stop the camera connection within frame1
stop_camera_button = ttk.Button(frame1, text="Stop Camera", command=stop_camera)
stop_camera_button.grid(row=1, column=0)

# Label to display camera connection state within frame1
camera_label = ttk.Label(frame1, text="Camera: Not Connected", foreground="red")
camera_label.grid(row=0, column=1, rowspan=2)

#ModBus Components
# Add an empty label and entry for IP address
ip_label = ttk.Label(ip_frame, text="IP Address:")
ip_label.grid(row=0, column=0)

ip_var = tk.StringVar()
ip_entry = ttk.Entry(ip_frame, textvariable=ip_var)
ip_entry.grid(row=0, column=1)

# Add an entry for port
port_label = ttk.Label(ip_frame, text="Port:")
port_label.grid(row=1, column=0)

port_var = tk.IntVar()
port_entry = ttk.Entry(ip_frame, textvariable=port_var)
port_entry.grid(row=1, column=1)

#button IP frame
bnt_ip_frame = ttk.Frame(ip_frame)
bnt_ip_frame.grid(row=2, column=0, columnspan=3)
# Create a Connect button for IP address
connect_button = ttk.Button(bnt_ip_frame, text="Connect to IP", command=start_ipconnect)
connect_button.grid(row=0, column=0)
# Create a Disconnect button for IP address
disconnect_button = ttk.Button(bnt_ip_frame, text="Disconnect from IP", command=stop_ipconnect)
disconnect_button.grid(row=0, column=1)

# Label to display serial connection state within frame1
ip_connect_label = ttk.Label(ip_frame, text=" IP: Not Connected", foreground="red")
ip_connect_label.grid(row=0, column=2, rowspan=2)

# Your camera and serial thread functions go here
def camera_thread_function(folder_path):
    global frame
    while not camera_stopped.is_set():
        ret, frame = cap.read()
        if ret:
            cv2.imshow("Webcam", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_camera()
                stop_ipconnect()
                break

def ip_thread_function():
    global prev_state, i, frame, modbusClient, registers
    while not ip_stopped.is_set():
        registers = modbusClient.read_holding_registers(9, 1)
        if registers is not None:
            line = int(''.join(map(str, registers)))
            # print(f"Parsed line: {line}")
            state = line
        else:
            print("Failed to read holding registers.")
            continue

        # if not line:
        #     continue

        # try:
        #     state = int(line)
        # except ValueError:
        #     print(f"Invalid data received from the IP port: {line}")
        #     continue

        print(f"Received state: {state}")

        if prev_state is not None and prev_state == 0 and state == 16256:
            screen_path = os.path.join(screen_fol, f'{screen_fol}_{i}.png')
            if frame is not None:
                cv2.imwrite(screen_path, frame)
                print(f'Screenshot taken: {screen_path}')
                i += 1
                root.after(500, display_screenshots)

        prev_state = state
        # time.sleep(0.1)

camera_stopped = threading.Event()  # Event to signal camera thread to stop
ip_stopped = threading.Event()  # Event to signal serial thread to stop

# After the Tkinter main loop, release resources and close threads
# root.protocol("WM_DELETE_WINDOW", stop_program)
root.mainloop()  # Start the GUI main loop