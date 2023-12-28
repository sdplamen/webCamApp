# Import required modules
import asyncio
import threading
import serial
import cv2
from flask import Flask, render_template
from flask_socketio import SocketIO
import sqlite3
from datetime import datetime
import pyautogui  # Added for mouse coordinates

# Initialize Flask application and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Initialize serial connection
ser = serial.Serial('COM1', baudrate=9600)  # Adjust COM port accordingly
cap = cv2.VideoCapture(0) # Adjust camera index accordingly

# Initialize SQLite database connection
conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# Create a table to store data
cursor.execute('''
    CREATE TABLE IF NOT EXISTS data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        mouse_x INTEGER,
        mouse_y INTEGER,
        image_path TEXT
    )
''')
conn.commit()

# Function to read serial data
def read_serial_data():
    while True:
        serial_data = ser.readline().decode('utf-8').strip()
        # Process serial data as needed
        # For example, you can extract mouse coordinates and send them via WebSocket
        mouse_x, mouse_y = pyautogui.position()
        socketio.emit('serial_data', {'coordinates': serial_data, 'mouse_x': mouse_x, 'mouse_y': mouse_y})

# Function to capture webcam image
def capture_webcam_image():
    while True:
        ret, frame = cap.read()

        # Process the frame as needed
        # For example, save the image and store the path in the database

        image_path = f'images/{datetime.now().strftime("%Y%m%d%H%M%S")}.jpg'
        cv2.imwrite(image_path, frame)
        socketio.emit('webcam_image', {'image_path': image_path, 'mouse_x': mouse_x, 'mouse_y': mouse_y})
    
        # Save data to SQLite database
        cursor.execute('''
            INSERT INTO data (mouse_x, mouse_y, image_path)
            VALUES (?, ?, ?)
        ''', (mouse_x, mouse_y, image_path))
        conn.commit()

# Background task to run parallel processes
async def background_task():
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(None, read_serial_data),
        loop.run_in_executor(None, capture_webcam_image),
    ]
    await asyncio.gather(*tasks)

# Route to serve the HTML page
@app.route('/')
def index():
    return render_template('index.html')

# WebSocket event handler
@socketio.on('connect')
def handle_connect():
    print('Client connected')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(background_task())
    socketio.run(app, debug=True)
