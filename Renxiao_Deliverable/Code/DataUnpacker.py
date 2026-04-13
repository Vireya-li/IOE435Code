from abc import ABC
from enum import Enum
from itertools import accumulate
import struct
from copy import deepcopy

"""
Takes input data and breaks the variables into bytes for transmissions, along with information about the data
Packet format
- Num variables, variable formats (Byte per variable), variable types (Byte per variable), Variable data (number depends on data type)
    - Variable format (0bTTTTSSSS) 
        - SSSS is the number of bytes in binary so 32 bit would be 4 bytes or 0100 and one byte would be 0001.
        - TTTT is the type of data
            - 1 unsigned int (short and long are determined by the number of bytes) int.from_bytes(bytes, byteorder='big', *, signed=False)
            - 2 int (short and long are determined by the number of bytes) int.from_bytes(bytes, byteorder='big', *, signed=True)
            - 3 char byte.encode
            - 4 float (double and long double are determined by the number of bytes) float.fromhex()
    - Variable source
        - 1 Timestamp
        - 2 Accl x
        - 3 Accl y
        - 4 Accl z
        - 5 Gyro x
        - 6 Gyro y
        - 7 Gyro z
        - 8 Mag x
        - 9 Mag y
        - 10 Mag z
        - 11 Temperature
        - 12 EMG
        
    - Variable data - all data is packed big endian as this is intended for a network protocol
        - The number 1023 (0x3ff in hexadecimal) has the following byte representations:
            - 03 ff in big-endian
            - ff 03 in little-endian
    Python can use struct.py to unpack the data

P. Pridham    
"""               

# DATA_PACKER_OVERHEAD_BYTES = 1
# DATA_PACKER_VARIABLE_INFO_BYTES = 2

# contains vector of data 

VERBOSE = False

class NAxisSensor:#(ABC):
    """
    A class to store a sensor information with multiple axes, typically 3 but doesn't have to be.  As data comes in it is appended to the end of the time series up to the size set (default 500).
    
    ...
    
    Attributes
    ----------
    num_axes : int
        The number of axes the sensor has.
    length : int
        The number of points in the time series data. Default is 500.
    timestamp : list
        Used to store data timestamps. New points are appended to the end of the list.  When the list is at the prescribed length the oldest value is removed to maintain a consistent size.
    data : list
        Data from the sensor.  Works in the same way as the timestamp but has num_axes of data added.
    data_transpose : list
        The data transposed.  This can make it easier to use in some places.
    max_val : float
        Tracks the max value that has been in the data.  This was to help with plotting data to set the plot axis range.
    min_val : float
        Tracks the min value that has been in the data.  This was to help with plotting data to set the plot axis range.
    
    Methods
    -------
    set_val(timestamp, data)
        When new data comes in you can add the data point to the sensor.
    reset_range()
        resets the max_val and min_val to 0.
    
    Static Methods
    -------
    None
    """
    
    def __init__(self, size = 500, data = 0, timestamp = 0):
        """
        Constructor for the NAxisSensor. Parameters can be set or left as defaults.  If defaults are used it will be a 1 axis sensor.
        
        Parameters
        ----------
        Keyword Arguments:
        size : int
            The largest number of points allowed in the time series data. Default is 500.
        data : list
            Data to initialize the data attribute with.  Defaults to 0.
        timestamp : int
            timestamp to initialize the data attribute with. Defaults to 0.
        
        Returns 
        -------
        None 
        """
        
        if type(data) is list:
            self.num_axes = len(data)
        else:
            self.num_axes = 1
        self.length = size
        self.timestamp = []
        self.data = []
        self.data_transpose = []
        self.timestamp.append(timestamp)
        self.data.append(data)
        self.max_val = 0
        self.min_val = 0
        
        return
        
    def set_val(self, timestamp, data):
        """
        Parameters
        ----------
        timestamp : int
            Timestamp for the data being added to the sensor.
        data : list
            Data point to be added to the sensor.
        
        Returns 
        -------
        None
        """        
        if VERBOSE:
            print('\n\nNAxisSensor :: set_val : at Top')
            print('\t Time List before append = ', self.timestamp)
            print('\t Data List before append = ', self.data)
        d = deepcopy(data) # used because python passes by reference so all the values were changed if the same list is updated and passed.
        self.timestamp.append(timestamp)
        self.data.append(d)
        if self.num_axes>1:
            self.min_val = min(self.min_val,min(d))
            self.max_val = max(self.max_val,max(d))
        else:
            self.min_val = min(self.min_val,d)
            self.max_val = max(self.max_val,d)
            
        if VERBOSE:
            print('NAxisSensor :: set_val :\n\t Time Input= ', timestamp)
            print('\t Time List= ', self.timestamp)
            print('\t Data Input= ', data)
            print('\t Data List = ', self.data)
        
        if len(self.timestamp)>self.length:
            del self.timestamp[0]
            del self.data[0]
        
        if self.num_axes>1:     
            self.data_transpose = list(map(list, zip(*self.data)))
        else:
            self.data_transpose = self.data
            
        return
    
    def reset_range(self):
        """
        Resets the max_val and min_val to zero.
        
        Parameters
        ----------
        None
        
        Returns 
        -------
        None 
        """
        self.max_val = 0
        self.min_val = 0
        return

class DataUnpacker:
    """
    A class used to unpack data in the form at the top of the document.  Contains class attributes that are used to decode the message and should be consistent with how the message is packaged in the sensor, along with a set of static methods used to decode the data packet.  For most cases you will just use unpack_data(data) to return the decoded values and data sources from the whole data packet.

    ...

    Attributes
    ----------
    Class Attributes:
    TypeCode : Enum
        Starts at 1 with uint, int, char, and float.
    SourceCode : Enum
        Starts at 1 with timestamp, accl_x, accl_y, accl_z, gyro_x, gyro_y, gyro_z, mag_x, mag_y, mag_z, temp, and emg.
    overhead_bytes : int
        The first byte of the message stores the number of variables.  Currently 1 byte but could be extended for larger sensor networks.
    variable_info_bytes : int
        Each variable has information about its format and type. Currently 2 per variable.  Details can be found in the packet format at the top of this document.

    Static Methods
    --------------
    unpack_data(data)
        Takes a raw data packet and extracts the data values and sources.
    get_variable_type(data, var_number = None)
        Gets the variable type from a raw data package.  If the variable number is not set it returns a list of the types for all variables, otherwise just returns the variable type for the specified variable number.
    get_var_start_stop_idx(data, size_array = None, var_number = None)
        Gets the start and stop index of the variable value bytes in the raw data packet.  If a specific variable is requested it returns a list with the start and stop indices.  If no variable is requested will return a list with a list of start indices and a list of stop indices.
    get_variable_size(data, var_number = None)
        Gets the number of bytes in the variable value. If a specific variable is requested it returns a list with the number of bytes in that variable.  If no variable is requested will return a list with the size of all the variables.
    get_variable_source(data, var_number = None)
        Gets the source of the variable. If a specific variable is requested it returns the source number for that variable.  If no variable is requested will return a list source number all the variables.
    get_variable_value(buff, var_type, var_size)
        Takes in a buffer with the value bytes for a specific variable, along with the variable type and size.  Returns the decoded value.
    """        
    TypeCode = Enum('TypeCode',['uint', 'int', 'char', 'float'], start = 1)
    SourceCode = Enum('SourceCode',['timestamp', 'accl_x', 'accl_y', 'accl_z', 'gyro_x', 'gyro_y', 'gyro_z', 'mag_x', 'mag_y', 'mag_z', 'temp', 'emg'], start = 1)
    overhead_bytes = 1
    variable_info_bytes = 2
    
    def unpack_data(data):
        """
        Takes a raw data packet and extracts the data values and sources.
        
        Parameters
        ----------
        data : bytearray
            Raw data packet from the sensor.  Formatted in the way described at the top of the file.
        Returns 
        -------
        data_vals : list
            A list of the values in the data packet.  Indices match the var_source indices.
        var_source : list
            List of the variable sources (integers) as described at the top of the document.  Indices match the data_val indices
        """
        num_var = data[0]
        if VERBOSE:
            print('---DataUnpacker.unpack_data() : num_var = ', num_var)
        var_type = DataUnpacker.get_variable_type(data)
        if VERBOSE:
            print('---DataUnpacker.unpack_data() : var_type = ', var_type)
        var_size = DataUnpacker.get_variable_size(data)
        if VERBOSE:
            print('---DataUnpacker.unpack_data() : var_size = ', var_size)
        var_source = DataUnpacker.get_variable_source(data)
        if VERBOSE:
            print('---DataUnpacker.unpack_data() : var_source = ', var_source)
        [var_start_idx, var_stop_idx] = DataUnpacker.get_var_start_stop_idx(data, var_size)
        data_vals = []
        
        for var in range(0,num_var):
            buff = data[var_start_idx[var]:var_stop_idx[var]]
            data_vals.append(DataUnpacker.get_variable_value(buff, var_type[var], var_size[var]))
        if VERBOSE:
            print('---DataUnpacker.unpack_data() : data_vals = ', data_vals)
        return data_vals, var_source

    def get_variable_type(data, var_number = None):
        """
        Gets the variable type from a raw data package.
        
        Parameters
        ----------
        data : bytearray
            Raw data packet from the sensor.  Formatted in the way described at the top of the file.
        Keyword Arguments:
        var_number : int
            Index of a specific variable of interest.  Should be less than num_var. Defaults to None
        Returns 
        -------
        type_info : list
            List of the types for all variables unless a specific variable number is specified.
        """
        type_info = []
        if var_number == None :
            check_range = range(0,data[0])
        
        else:
            check_range = range(var_number, var_number+1)
            
        for var_num in check_range:
            full_byte = data[DataUnpacker.overhead_bytes + var_num]
            if VERBOSE:
                print('---DataUnpacker.get_variable_type() : var_num = ', var_num, ' full_byte is ', full_byte)
            nible = full_byte>>4&0x0F
            if VERBOSE:
                print('---DataUnpacker.get_variable_type() : var_num = ', var_num, ' nible is ', nible)
            type_info.append(nible)
            
        return type_info
        
    def get_var_start_stop_idx(data, size_array = None, var_number = None):
        """
        Gets the start and stop index of the variable value bytes in the raw data packet.
        
        Parameters
        ----------
        data : bytearray
            Raw data packet from the sensor.  Formatted in the way described at the top of the file.
        Keyword Arguments:
        size_array : list
            list of the size of the variables, can be retrieved from get_variable_size(data)
        var_number : int
            Index of a specific variable of interest.  Should be less than num_var. Defaults to None
        
        Returns 
        -------
        start_stop_idx : list
            List with a list of start indices and a list of stop indices of all the variables value bytes if no specific variable is requested.  If a variable is specified it is just a list with the variables start and stop indices.
        """
        if size_array == None:
            size_array = get_variable_size(data)
            
        full_stop_idx = [DataUnpacker.overhead_bytes + DataUnpacker.variable_info_bytes*data[0] + val for val in list(accumulate(size_array))]
        full_start_idx = [stop_idx - size for stop_idx, size in zip(full_stop_idx, size_array)]
        
        if var_number == None :
            start_stop_idx = [full_start_idx, full_stop_idx]
        
        else:
            start_stop_idx = [full_start_idx[var_number], full_stop_idx [var_number] ]
            
        return start_stop_idx
        

    def get_variable_size(data, var_number = None):
        """
        Gets the number of bytes in the variable value.
        
        Parameters
        ----------
        data : bytearray
            Raw data packet from the sensor.  Formatted in the way described at the top of the file.
        Keyword Arguments:
        var_number : int
            Index of a specific variable of interest.  Should be less than num_var. Defaults to None
        
        Returns 
        -------
        size_info : list
            list with the number of bytes for the value of each variable.  If a specific variable is requested is a list with that variables data.
        """
        size_info = []
        if var_number == None :
            check_range = range(0,data[0])
        
        else:
            check_range = range(var_number, var_number+1)
            
        for var_num in check_range:
            full_byte = data[DataUnpacker.overhead_bytes + var_num]
            nible = full_byte&0x0F
            size_info.append(nible)
            
        return size_info
        
    def get_variable_source(data, var_number = None):
        """
        Gets the source of the variable.
        
        Parameters
        ----------
        data : bytearray
            Raw data packet from the sensor.  Formatted in the way described at the top of the file.
        Keyword Arguments:
        var_number : int
            Index of a specific variable of interest.  Should be less than num_var. Defaults to None
        
        Returns 
        -------
        source_info : list
            If a specific variable is requested it returns the source number for that variable.  If no variable is requested will return a list source number for all the variables.
        """
        source_info = []
        if var_number == None :
            check_range = range(0,data[0])
        
        else:
            check_range = range(var_number, var_number+1)
            
        for var_num in check_range:
            full_byte = data[DataUnpacker.overhead_bytes+ data[0] + var_num]
            source_info.append(full_byte)
            
        return source_info
        
        
    def get_variable_value(buff, var_type, var_size):
        """
        Returns the decoded data value for a specific variable
        
        Parameters
        ----------
        buff : bytearray
            bytearray that contains just the bytes containing the value for the variable.
        var_type : int
            Code for the type of data to be decoded.  Should align with the TypeCode attribute.
        var_size : int
            Number of bytes used for the variable value.
        Returns 
        -------
        val : different types 
            The decoded value for the variable of interest.
        """
        
        if var_type == DataUnpacker.TypeCode.uint.value:
            if var_size == 2:
                [val,] = struct.unpack('!H',buff)
            elif var_size == 4:
                [val,] = struct.unpack('!I',buff)
            elif var_size == 8:
                [val,] = struct.unpack('!Q',buff)
                
        elif var_type == DataUnpacker.TypeCode.int.value:
            if var_size == 2:
                [val,] = struct.unpack('!h',buff)
            elif var_size == 4:
                [val,] = struct.unpack('!i',buff)
            elif var_size == 8:
                [val,] = struct.unpack('!q',buff)
                
        elif var_type == DataUnpacker.TypeCode.char.value:
            val = chr(struct.unpack('!B',buff)[0])
            
        elif var_type == DataUnpacker.TypeCode.float.value:
            if var_size == 2:
                [val,] = struct.unpack('!e',buff)
            elif var_size == 4:
                [val,] = struct.unpack('!f',buff)
            elif var_size == 8:
                [val,] = struct.unpack('!d',buff)
        else:
            print("!!! unpack_data() : invalid type code : ", var_type)
            val = None
        return val

if __name__ == "__main__":
    # import ctype
    # not a true test since it is Python to Python but will allow testing of errors
    
    a = struct.pack('!c', str.encode('P')) # type 3 size 1
    b = struct.pack('!H', 13) # type 1 size 2
    c = struct.pack('!I', 14) # type 1 size 4
    d = struct.pack('!Q', 15) # type 1 size 8
    e = struct.pack('!h', 16) # type 2 size 2 
    f = struct.pack('!i', 17) # type 2 size 4 
    g = struct.pack('!q', 18) # type 2 size 8
    h = struct.pack('!e', 19) # type 4 size 2
    i = struct.pack('!f', 20) # type 4 size 4
    j = struct.pack('!d', 21) # type 4 size 8
    
    # 10 variables
    data = bytearray(0x0A.to_bytes(1,'big'))
    
    data.append(0x31)
    data.append(0x12)
    data.append(0x14)
    data.append(0x18)
    data.append(0x22)
    data.append(0x24)
    data.append(0x28)
    data.append(0x42)
    data.append(0x44)
    data.append(0x48)
    
    data.append(0x01)
    data.append(0x02)
    data.append(0x03)
    data.append(0x04)
    data.append(0x05)
    data.append(0x06)
    data.append(0x07)
    data.append(0x08)
    data.append(0x09)
    data.append(0x0A)

    

    data.extend(a)
    data.extend(b)
    data.extend(c)
    data.extend(d)
    data.extend(e)
    data.extend(f)
    data.extend(g)
    data.extend(h)
    data.extend(i)
    data.extend(j)
    
    vals, sources = DataUnpacker.unpack_data(data)
    accl = [0]*3
    gyro = [0]*3
    mag = [0]*3
    temp = 0
    emg = 0
    for i in range(0,data[0]):
        if sources[i] == DataUnpacker.SourceCode.timestamp.value:
            time = vals[i]
        elif sources[i] == DataUnpacker.SourceCode.accl_x.value:
            accl[0] = vals[i]
        elif sources[i] == DataUnpacker.SourceCode.accl_y.value:
            accl[1] = vals[i]
        elif sources[i] == DataUnpacker.SourceCode.accl_z.value:
            accl[2] = vals[i]
        elif sources[i] == DataUnpacker.SourceCode.gyro_x.value:
            gyro[0] = vals[i]
        elif sources[i] == DataUnpacker.SourceCode.gyro_y.value:
            gyro[1] = vals[i]
        elif sources[i] == DataUnpacker.SourceCode.gyro_z.value:
            gyro[2] = vals[i]
        elif sources[i] == DataUnpacker.SourceCode.mag_x.value:
            mag[0] = vals[i]
        elif sources[i] == DataUnpacker.SourceCode.mag_y.value:
            mag[1] = vals[i]
        elif sources[i] == DataUnpacker.SourceCode.mag_z.value:
            mag[2] = vals[i]
        elif sources[i] == DataUnpacker.SourceCode.temp.value:
            temp = vals[i]
        elif sources[i] == DataUnpacker.SourceCode.emg.value:
            emg = vals[i]
    
    print('time = ', time)
    print('accl = ', accl)
    print('gyro = ', gyro)
    print('mag = ', mag)
    print('temp = ', temp)
    print('emg = ', emg)
        
        
    