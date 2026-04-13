from DataUnpacker import *
import os
import socket
import time
from DataLogger import *
from copy  import deepcopy
#import threading 
"""
P. Pridham
"""
class UDPHandler:
    """
    Class that handles UDP data packages from sensors.  Unpacks the data using DataUnpacker.  And if a flag is set to record the data records it using the DataLogger.
    
    ...
    Class Attributes
    ----------------
    udp_port : int
        Port the socket listen to.  Needs to match the port the sensor is sending to.
    data_size
        Size to make the sensor record up to that can be accessed for plotting.  Sensor currently works at 100 Hz so 500 is roughly 5 seconds.
    
    Attributes
    ----------
    sock : socket
        The socket used to receive the UDP data on.
    current_data : dict
        Dictionary to contain the most recent data that came in after being decoded.
    data_path : string
        Path for where the data where be written
    base_name : string
        Base filename the data will be saved to.  A timestamp will be added to the base.
    log_data : bool
        Data will be logged when true
    prev_log_data : bool
        Previous state of log_data to check for change.
    logger : DataLogger
        DataLogger instance that manages the data logging.
    timeout_s : float
        The number of seconds that need to pass without receiving data to be considered a lost connection.
    time_data_received : time
        The time data was last received, used with timeout_s and the current time to determine timeout
    pulse_s : float
        Time in seconds between sending out a UDP packet (heartbeat) on the port to keep it open on the computer.
    last_heartbeat : time
        Time the last UDP packet (heartbeat) was sent out from the computer. 
    receiving : list bool
        Value to track if data is coming in.  Is true unless a packet isn't received in the timeout period.
    start_time : time
        Timestamp of the first data packet used to offset the time data.
    data_came_in : bool
        Used to track if the packet that came in was data or the heartbeat.
    accl_sensor : NAxisSensor
        3 axis sensor used to record the accelerometer data
    gyro_sensor : NAxisSensor
        3 axis sensor used to record the gyroscope data
    mag_sensor : NAxisSensor
        3 axis sensor used to record the magnetometer data
    temp_sensor : NAxisSensor
        1 axis sensor used to record the temperature data
    emg_sensor : NAxisSensor
        1 axis sensor used to record the EMG data    
    
    Methods
    -------
    __init__()
        Constructor for the instance of UDPHandler
    __del__()
        Deconstructor for the instance of the UDPHandler
    keep_alive()
        Checks when the last heartbeat was sent and if it is due sends out a packet with just 0 in it.
    unpack_data()
        Unpacks the data from the packet received, places it in current_data, and manages logging the new data if required.
    handler(kill_thread)
        A handler that can be used in a thread and will run contentiously until kill_thread is set.  Just calls handler_one_shot in a loop.
    handler_one_shot()
        Checks heartbeat, timeout, if packets came in, unpacks the data, and adds the data to the sensors.
    on_finished()
        Called when the program is ready to close and closes the socket.  Closing the socket with the deconstructor doesn't work. 
    on_error(error_string)
        Called when there is an error, to show it.  Currently unused.
    on_result(result)
        Called when there is a result.  Currently unused.
        
    Static Methods
    --------------
    None
    """
    # UDP_IP = '192.168.1.4'
    udp_port = 64346
    data_size = 500
    
    def __init__(self):
        """
        Constructor for the UDPHandler. 
        
        Parameters
        ----------
        None
        
        Returns 
        -------
        None 
        """
        self.sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP
        self.sock.setblocking(False)
        self.sock.bind(('', UDPHandler.udp_port))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # setup sensors using dict for the data logger
        self.current_data = {
            "timestamp": 0,
            "accl_x": 0,
            "accl_y": 0,
            "accl_z": 0,
            "gyro_x": 0,
            "gyro_y": 0,
            "gyro_z": 0,
            "mag_x": 0,
            "mag_y": 0,
            "mag_z": 0,
            "temp": 0,
            "emg": 0
            }
            
        self.data_path = 'Data'
        self.base_name = 'IMU'
        
        self.log_data = False
        self.prev_log_data = False
        self.logger = DataLogger(self.current_data, path = self.data_path, base_name = self.base_name) 
        
        self.timeout_s = .1
        self.time_data_received = 0
        self.pulse_s = 10
        self.last_heartbeat = -self.pulse_s # force first heartbeat
        self.receiving = [False] # needed so the thread passes by reference
        
        self.start_time = 0
        sensors_created = False
        self.data_came_in = False
        # TODO if windows send 2 packets that are just 0 to make sure port is listened to.
        # if os.name == 'nt':
            # # just broadcasting to make it easier since the other ports will need to ignore it anyways, could send it to the gateway, but I don't want to hardcode the address or search the gateway.
            # self.sock.sendto((0).to_bytes(), ('192.168.4.1', UDPHandler.udp_port)) 
            # self.sock.sendto((0).to_bytes(), ('192.168.4.1', UDPHandler.udp_port))
            
        while not sensors_created:
            try:
                self.keep_alive()
                self.data, addr = self.sock.recvfrom(1024) # buffer size is 1024 bytes
                self.data_came_in = True
            except KeyboardInterrupt:
                sock.close()
            except:
                # print("Unexpected error:", sys.exc_info()[0] )
                pass  
            # print("--UDPHandler :: __init__ : waiting for data")    
            if self.data_came_in and self.data[0] != 0: # moving this outside the try to get error statements
                # print("--UDPHandler :: __init__ : data came in")
                self.data_came_in = False
                self.unpack_data()
                
                self.start_time = self.current_data["timestamp"]
                self.accl_sensor = NAxisSensor(data=[self.current_data["accl_x"],self.current_data["accl_y"],self.current_data["accl_z"]],timestamp = 0, size = UDPHandler.data_size)
                self.gyro_sensor = NAxisSensor(data=[self.current_data["gyro_x"],self.current_data["gyro_y"],self.current_data["gyro_z"]],timestamp = 0, size = UDPHandler.data_size)
                self.mag_sensor = NAxisSensor(data=[self.current_data["mag_x"],self.current_data["mag_y"],self.current_data["mag_z"]],timestamp = 0, size = UDPHandler.data_size)
                self.temp_sensor = NAxisSensor(data=self.current_data["temp"],timestamp = 0, size = UDPHandler.data_size)
                self.emg_sensor = NAxisSensor(data=self.current_data["emg"],timestamp = 0, size = UDPHandler.data_size) 
                
                sensors_created = True
    def __del__(self): # this doesn't seem to be getting called.
        """
        Deconstructor for the UDPHandler. Just closes the socket. 
        
        Parameters
        ----------
        None
        
        Returns 
        -------
        None 
        """
        self.sock.close()
        print('-- UDPHandler - __del__ : socket closed')
        
    def keep_alive(self):
        """
        Checks when the last heartbeat was sent and if it is due sends out a packet with just 0 in it.
        
        Parameters
        ----------
        None
        
        Returns 
        -------
        None 
        """
        if time.time() - self.last_heartbeat > self.pulse_s : # keeps port open on windows.
            if os.name == 'nt':
                # just broadcasting to make it easier since the other ports will need to ignore it anyways, could send it to the gateway, but I don't want to hardcode the address or search the gateway.
                self.sock.sendto((0).to_bytes(), ('255.255.255.255', UDPHandler.udp_port))
            self.last_heartbeat = time.time()
        
    def unpack_data(self):
        """
        Unpacks the data from the packet received, places it in current_data, and manages logging the new data if required.
        
        Parameters
        ----------
        None
        
        Returns 
        -------
        None 
        """
        vals, sources = DataUnpacker.unpack_data(self.data)
        new_data = False # used to check if data actually came in.
        
        for i in range(0,self.data[0]):
            if sources[i] == DataUnpacker.SourceCode.timestamp.value:
                self.current_data["timestamp"] = vals[i]-self.start_time
                new_data = True # the source has data and it isn't just the heartbeat.
            elif sources[i] == DataUnpacker.SourceCode.accl_x.value:
                self.current_data["accl_x"] = vals[i]
            elif sources[i] == DataUnpacker.SourceCode.accl_y.value:
                self.current_data["accl_y"] = vals[i]
            elif sources[i] == DataUnpacker.SourceCode.accl_z.value:
                self.current_data["accl_z"] = vals[i]
            elif sources[i] == DataUnpacker.SourceCode.gyro_x.value:
                self.current_data["gyro_x"] = vals[i]
            elif sources[i] == DataUnpacker.SourceCode.gyro_y.value:
                self.current_data["gyro_y"] = vals[i]
            elif sources[i] == DataUnpacker.SourceCode.gyro_z.value:
                self.current_data["gyro_z"] = vals[i]
            elif sources[i] == DataUnpacker.SourceCode.mag_x.value:
                self.current_data["mag_x"] = vals[i]
            elif sources[i] == DataUnpacker.SourceCode.mag_y.value:
                self.current_data["mag_y"] = vals[i]
            elif sources[i] == DataUnpacker.SourceCode.mag_z.value:
                self.current_data["mag_z"] = vals[i]
            elif sources[i] == DataUnpacker.SourceCode.temp.value:
                self.current_data["temp"] = vals[i]
            elif sources[i] == DataUnpacker.SourceCode.emg.value:
                self.current_data["emg"] = vals[i]
                
        if (not self.prev_log_data) and self.log_data:
            self.logger.new([self.current_data], path = self.data_path, base_name = self.base_name)
        if self.log_data and new_data:
            self.logger.log([self.current_data])
            
        self.prev_log_data = self.log_data
                
        return
    
    def handler(self, kill_thread):
        """
        A handler that can be used in a thread and will run contentiously until kill_thread is set.  Just calls handler_one_shot in a loop.
        
        Parameters
        ----------
        kill_thread : threading.event
            While the kill_thread event is not set the loop runs.
            
        Returns 
        -------
        None 
        """
        while not kill_thread.is_set(): # handler just repeatedly runs.  Needs to be in a different thread if you want to do anything else.
            self.handler_one_shot()
        if kill_thread.is_set() :
            self.sock.close()
            print('-- UDPHandler - handler : thread killed, socket closed')
            return
            
    def handler_one_shot(self):
        """
        Checks heartbeat, timeout, if packets came in, unpacks the data, and adds the data to the sensors.
        
        Parameters
        ----------
        None
        
        Returns 
        -------
        None 
        """
        try:
            # print("UDPHandler :: handler : checking for data ")
            self.keep_alive()
            if time.time() - self.time_data_received > self.timeout_s :
                self.receiving[0] = False
            
            if time.time() - self.time_data_received > self.timeout_s :
                self.receiving[0] = False
                # print("--> UDPHandler :: handler : receiving = ", self.receiving)
            self.data, addr = self.sock.recvfrom(1024) # buffer size is 1024 bytes
            self.data_came_in = True

        except BlockingIOError: 
            # no connection
            # print("blocking error:")
            pass
        
        # except KeyboardInterrupt:
            # sock.close()
            
        if self.data_came_in: # moving this outside the try to get error statements
            self.data_came_in = False
            self.unpack_data()
            self.time_data_received = time.time()
            self.receiving[0] = True
            
            # print("UDPHandler :: handler : Data came in - Timestamp = ", self.current_data["timestamp"])
            self.accl_sensor.set_val(self.current_data["timestamp"],[self.current_data["accl_x"],self.current_data["accl_y"],self.current_data["accl_z"]])
            self.gyro_sensor.set_val(self.current_data["timestamp"],[self.current_data["gyro_x"],self.current_data["gyro_y"],self.current_data["gyro_z"]])
            self.mag_sensor.set_val(self.current_data["timestamp"],[self.current_data["mag_x"],self.current_data["mag_y"],self.current_data["mag_z"]])
            self.temp_sensor.set_val(self.current_data["timestamp"],self.current_data["temp"])
    
        return
        
    def on_finished(self):
        """
        Called when the program is ready to close and closes the socket.  Closing the socket with the deconstructor doesn't work. 
        
        Parameters
        ----------
        None
        
        Returns 
        -------
        None 
        """
        print("Function execution finished")
        self.sock.close()
        print('-- UDPHandler - handler : thread killed, socket closed')

    def on_error(self, error_string):
        """
        Called when there is an error, to show it.  Currently unused.
        
        Parameters
        ----------
        None
        
        Returns 
        -------
        None 
        """
        print(f"Error: {error_string}")

    def on_result(self, result):
        """
        Called when there is a result.  Currently unused.
        
        Parameters
        ----------
        None
        
        Returns 
        -------
        None 
        """
        # print(f"Result: {result}")
        return
            
if __name__ == '__main__':
    udp = UDPHandler()
    udp.log_data = True
    udp.handler()