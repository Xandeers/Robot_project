import socket
import cv2
import numpy as np
import struct
from camera.terrain import Terrain


# Configuration
ip = ""  # listen to all interfaces
port = 8080
MaximumPacketSize = 1400

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ip, port))

print("Listening for UDP frames...")


terrain_manager = Terrain(num_zones=2, points_per_zone=8)
window_name = "Received Frame"
cv2.namedWindow(window_name)

cv2.setMouseCallback(window_name, terrain_manager.mouse_callback)

data_buffer = {}
current_frame_id = -1

messageHeader = 4
headerSize = 8

while True:
    try:
        packet, addr = sock.recvfrom(MaximumPacketSize)
        packet_id, frame_id = struct.unpack('II', packet[:headerSize])
        payload = packet[headerSize:]

        if frame_id != current_frame_id:
            if current_frame_id != -1 and current_frame_id + 1 == frame_id:
                # Reconstruct the full frame
                full_data = b''.join([data_buffer[i] for i in sorted(data_buffer)])
                frame_data = full_data[messageHeader:]
                frame_buffer = np.frombuffer(frame_data, dtype=np.uint8)
                frame = cv2.imdecode(frame_buffer,1)
                if frame is not None:


                    frame = terrain_manager.draw_zones(frame)
                    
                    #option calibrage
                    if len(terrain_manager.points) < 16:
                        cv2.putText(frame, f"Calibration: {len(terrain_manager.points)}/16", 
                                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                    cv2.imshow("Received Frame", frame)
                    ch = chr(cv2.waitKey(int(1)) & 0xFF)
                    if ch=='q' or ch=='Q': break
            
            # Reset buffer for new frame
            data_buffer = {}
            current_frame_id = frame_id

        data_buffer[packet_id] = payload
    except socket.error:
        continue

sock.close()
cv2.destroyAllWindows()
