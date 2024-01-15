import cv2
import os
import serial
import threading
import tkinter as tk
from tkinter import ttk
from itertools import cycle
from PIL import Image, ImageTk
import serial.tools.list_ports

screen_fol = 'screen'
i = 1
prev_state = None
frame = None  # Initialize frame as None
state = None
line = '0'
image_matrix = [[1, 10, 11, 20, 21, 30, 31, 40],
                [2, 9, 12, 19, 22, 29, 32, 39],
                [3, 8, 13, 18, 23, 28, 33, 38],
                [4, 7, 14, 17, 24, 27, 34, 37],
                [5, 6, 15, 16, 25, 26, 35, 36]]

if not os.path.exists(screen_fol):
    os.makedirs(screen_fol)

# Create a GUI window
root = tk.Tk()
root.geometry('1200x550')
root.title("Camera and Serial Monitor")

# Create a frame to contain the components
frame1 = ttk.Frame(root)
frame1.grid(row=0, column=0)

frame2 = ttk.Frame(root)
frame2.grid(row=0, column=1)

# Create a frame for serial connection within frame1
serial_frame = ttk.Frame(frame1)  # Changed from serial_frame = ttk.Frame(root)
serial_frame.grid(row=3, column=0)

# Function to get a list of available COM ports
def get_available_com_ports():
    try:
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports
    except Exception as e:
        print('Error getting availiable COM ports: {e}')
        return []

# Function to update the COM port dropdown menu
def update_com_ports():
    com_ports = get_available_com_ports()
    com_dropdown['values'] = com_ports
    if com_ports:
        com_dropdown.current(0)  # Set the default selection to the first available port
    else:
        com_dropdown.set('')  # Clear the selection if no ports are available

# Dropdown menu for selecting COM port
com_label = ttk.Label(serial_frame, text="Select COM Port:")
com_label.grid(row=1, column=0)

com_ports = get_available_com_ports()  # Get available COM ports initially
selected_com_port = tk.StringVar()
com_dropdown = ttk.Combobox(serial_frame, textvariable=selected_com_port, values=com_ports)
com_dropdown.grid(row=1, column=1, columnspan=2)
com_dropdown.current(0)  # Set the default selection

# Add this line to update the COM ports initially
update_com_ports()

# Set the default selection to the first available port if there are any
if com_ports:
    com_dropdown.current(0)
else:
    com_dropdown.set('')  # Clear the selection if no ports are available

# Function to update camera connection state
def update_camera_state():
    if cap.isOpened():
        camera_label.config(text="Camera: Connected", foreground="green")
    else:
        camera_label.config(text="Camera: Not Connected", foreground="red")

# Function to update serial connection state
def update_serial_state():
    if ser.is_open:
        serial_label.config(text="Serial: Connected", foreground="green")
    else:
        serial_label.config(text="Serial: Not Connected", foreground="red")

# Function to start the camera connection
def start_camera():
    global cap
    cap = cv2.VideoCapture(1)  # Open the camera
    if cap.isOpened():
        update_camera_state()

    camera_thread = threading.Thread(target=camera_thread_function)
    camera_thread.start()

# Function to stop the camera connection
def stop_camera():
    global cap
    if cap.isOpened():
        cap.release()
        update_camera_state()

# Function to start the serial connection
def start_serial():
    global ser
    selected_port = selected_com_port.get()
    ser = serial.Serial(selected_port, 115200)  # Open the selected serial port
    if ser.is_open:
        update_serial_state()
    serial_thread = threading.Thread(target=serial_thread_function)
    serial_thread.start()

# Function to stop the serial connection
def stop_serial():
    global ser
    if ser.is_open:
        ser.close()
        update_serial_state()

# Button to start the camera connection within frame1
start_camera_button = ttk.Button(frame1, text="Start Camera", command=start_camera)
start_camera_button.grid(row=0, column=0)

# Button to stop the camera connection within frame1
stop_camera_button = ttk.Button(frame1, text="Stop Camera", command=stop_camera)
stop_camera_button.grid(row=0, column=1)

# Button to start the serial connection within frame1
start_serial_button = ttk.Button(frame1, text="Start Serial", command=start_serial)
start_serial_button.grid(row=1, column=0)

# Button to stop the serial connection within frame1
stop_serial_button = ttk.Button(frame1, text="Stop Serial", command=stop_serial)
stop_serial_button.grid(row=1, column=1)

# Label to display camera connection state within frame1
camera_label = ttk.Label(frame1, text="Camera: Not Connected", foreground="red")
camera_label.grid(row=2, column=0)

# Label to display serial connection state within frame1
serial_label = ttk.Label(frame1, text="Serial: Not Connected", foreground="red")
serial_label.grid(row=2, column=1)

# Function to display the captured screenshots in the grid
def display_screenshots():
    # global image_matrix
    for row, image_row in enumerate(image_matrix):
        for col, image_num in enumerate(image_row):
            image_path = os.path.join(screen_fol, f'screen_{image_num}.png')
            if os.path.exists(image_path):
                img = Image.open(image_path)
                img = img.resize((100, 100), Image.LANCZOS)  # Resize the image with anti-aliasing
                img = ImageTk.PhotoImage(img)  # Convert to a format that tkinter can display

                # Create a label to display the image
                label = ttk.Label(frame2, image=img)
                label.grid(row=row, column=col)
                label.image = img  # Keep a reference to the image to prevent it from being garbage collected

# Your camera and serial thread functions go here
def camera_thread_function():
    global frame
    while not camera_stopped.is_set():
        ret, frame = cap.read()
        if ret:
            cv2.imshow("Webcam", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_camera()
                stop_serial()
                break

def serial_thread_function():
    global prev_state, i, frame
    while not serial_stopped.is_set():
        line = ser.readline().decode('utf-8').strip()
        if not line:
            # Handle empty string gracefully
            continue

        try:
            state = int(line)
        except ValueError:
            # Handle invalid data received from the serial port
            print(f"Invalid data received from the serial port: {line}")
            continue

        print(f"Received state: {state}")

        if prev_state is not None and prev_state == 0 and state == 1:
            screen_path = os.path.join(screen_fol, f'screen_{i}.png')
            if frame is not None:
                cv2.imwrite(screen_path, frame)
                print(f'Screenshot taken: {screen_path}')
                i += 1
                root.after(500, display_screenshots)

        prev_state = state
        
camera_stopped = threading.Event()  # Event to signal camera thread to stop
serial_stopped = threading.Event()  # Event to signal serial thread to stop

# After the Tkinter main loop, release resources and close threads
# root.protocol("WM_DELETE_WINDOW", stop_program)

root.mainloop()  # Start the GUI main loop