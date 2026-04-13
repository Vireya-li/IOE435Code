import os, sys
from datetime import datetime 

# P. Pridham July 2023

class DataLogger:
    """ 
    A class used to write data to a csv file.  Uses an array of dictionaries, writing the keys as the first row and the values in the following rows.  Does not track the fields so it is up to you to make sure the order of the dictionaries in the array are consistent

    ...

    Attributes
    ----------
    _file_base : string
        An addition to the timestamp used to track what the file is recording
    _file_extension : string
        Just '.csv'. Could be an option in the future.
    _max_file_size : int
        A value to limit the file size as some systems struggle with really large files.
    _data_filename : string  
        The name of the active file being written.
    _data_file : file object
        The file object for the currently open file.
    
    
    Methods
    -------
    __init__(data_to_log)
        Creates a new file and writes the dictionary keys to the first row.
    __del__()
        Calls _close() to close the open file.
    new(data_to_log)
        Creates a new file based on the current time and writes the dictionary keys to the first row.
    log(data_to_log)
        Takes in an array of dictionaries and writes the values to a csv file. If the filesize is too large it creates a file with an incremented name.
    
    _close()
        Closes the current open file.
        
    Static Methods
    -------
    _get_free_filename(base, extension)
        Checks if the base and extension file combination exists adding an _{number} where the number increments up till the file doesn't exist.
    _get_labels(data_to_log)
        Takes in an array of dictionaries and returns a comma separated string of the keys.
    _get_values(data_to_log)
        Takes in an array of dictionaries and returns a comma separated string of the values.
    """
    
    def __init__(self, data_to_log, path = '', base_name = '', max_file_size = 500 * 10**6):
        """
        Constructor for the data logger.  Initializes parameters and creates the file to write to.  Takes in an array of dictionaries that will be logged.  Keys from the dicts are the first row of the created csv files.  The path and an additional label to the name can be specified.  The maximum file size can be specified as well

        Parameters
        ----------
        data_to_log : Array of dicts
            The dictionaries to be logged.  These should be in the same order they will be sent to the logger every time as it will write in this order every time.
        
        Keyword Arguments:
        path : string
            If a location other than the directory where the file was open it can be specified here.  The path will be created if it doesn't exist already. Default is an empty string.
        base_name : string
            This will be added to the filename after the timestamp.  It can be used to specify a specific device, study name.  Default is an empty string.
        max_file_size : int
            The largest file size desired.  It is not a strict limit as the data will be written when the file is below this size. So the last line will bring the filesize over the limit.  Default is 500x10^6 (500 MB).
        
        Returns
        -------
        None 
        """
        self._file_base = ''
        self._file_extension = ".csv"
        
        self._max_file_size = -1
        
        self._data_filename = ''
        self._data_file = None
        # self.new(data_to_log, path = path, base_name = base_name, max_file_size = max_file_size)
        
    
    def __del__(self):
        """
        Destructor for the logger.  Just makes sure the current file is closed.

        Parameters
        ----------
        None
        
        Returns
        -------
        None 
        """
        self._close()
    
    def new(self, data_to_log, path = '', base_name = '', max_file_size = 500 * 10**6):
        """
        Creates a new file set to write to, releasing whatever the current file set is.  Works much like a reset of the constructor.  Takes in an array of dictionaries that will be logged.  Keys from the dicts are the first row of the created csv files.  The path and an additional label to the name can be specified.  The maximum file size can be specified as well

        Parameters
        ----------
        data_to_log : Array of dicts
            The dictionaries to be logged.  These should be in the same order they will be sent to the logger every time as it will write in this order every time.
        
        Keyword Arguments:
        path : string
            If a location other than the directory where the file was open it can be specified here.  The path will be created if it doesn't exist already. Default is an empty string.
        base_name : string
            This will be added to the filename after the timestamp.  It can be used to specify a specific device, study name.  Default is an empty string.
        max_file_size : int
            The largest file size desired.  It is not a strict limit as the data will be written when the file is below this size. So the last line will bring the filesize over the limit.  Default is 500x10^6 (500 MB).
        
        Returns
        -------
        None 
        """
        # Close the current file if it exists.
        if self._data_file != None:
            if not self._data_file.closed:
                self._close()
        # get a new timestamp   
        start_time = datetime.now()
        time_str = start_time.strftime("%Y_%m_%d_%Hh_%Mm_%Ss")
        if base_name != '':
            time_str += '_'
        
        # Create the path if it doesn't exist.
        if path != '' and not os.path.exists(path) : 
            os.makedirs(path)
        
        # save the concatenation of the path and filename components
        self._file_base = os.path.join(path, time_str + base_name)
        self._file_extension = ".csv"
        
        self._max_file_size = max_file_size
        
        # get the next filename and open it.
        self._data_filename = DataLogger._get_free_filename(self._file_base, self._file_extension)
        self._data_file = open(self._data_filename, 'a')
        
        # write the keys to the file.
        labels_csv = DataLogger._get_labels(data_to_log)
        self._data_file.write(labels_csv)
        self._data_file.write("\n ")
        # File stays open till we want to close.
    
    def log (self, data_to_log):
        """
        Takes in an array of dictionaries and writes the values to a csv file. If the filesize is too large it creates a file with an incremented name.
        Parameters
        ----------
        data_to_log : Array of dicts
            The dictionaries to be logged.  These should be in the same order they will be sent to the logger every time this will determine the order the columns are written.
                
        Returns
        -------
        None 
        """
        # check file size
        if self._data_file.tell() > self._max_file_size : # tell used instead of os.path.getsize since the file is open.
            self._data_file.close()
            # get the next filename and open it.
            self._data_filename = DataLogger._get_free_filename(self._file_base, self._file_extension)
            self._data_file = open(self._data_filename, 'a')
            # write the keys to the file.
            labels_csv = DataLogger._get_labels(data_to_log)
            self._data_file.write(labels_csv)
            self._data_file.write("\n ")
        # write the values to the file.
        values = DataLogger._get_values(data_to_log)
        self._data_file.write(values)
        self._data_file.write("\n ")
        
    def _close(self):
        """
        Closes the current open file.
        
        Parameters
        ----------
        data_to_log : Array of dicts
            The dictionaries to be logged.  These should be in the same order they will be sent to the logger every time this will determine the order the columns are written.
                
        Returns
        -------
        None 
        """
        if self._data_file is not None:
            self._data_file.close()
        
    def _get_free_filename(base, extension):
        """
        Checks if the base and extension file combination exists adding an _{number} where the number increments up till the file doesn't exist.
        
        Parameters
        ----------
        base : string
            The full filename, including the path, excluding the extension.  This is the part the increment will be added to if needed.
        extension : string
            The extension to use for the text file.  This will generally just be .csv, but this structure makes it more general.
                
        Returns
        -------
        data_filename : string
            A filename that does not exist, based on the base-extension combination adding an increment if needed.
        """
        data_filename = base + extension
        i = 0
        # check if the current combination exists, if it does increment and check again.
        while os.path.exists(data_filename):
            i +=1
            data_filename =  base + "_"+ str(i) + extension
        return data_filename
        
    def _get_labels(data_to_log):
        """
        Takes in an array of dictionaries and returns a comma separated string of the keys.
        
        Parameters
        ----------
        data_to_log : Array of dicts
            The dictionaries to be logged.  These should be in the same order they will be sent to the logger every time this will determine the order the columns are written.
                
        Returns
        -------
        labels : string
            A comma separated string of the keys from the provided dictionaries.
        """
        labels = ''
        # Go through all the dictionaries pulling all the keys of each one into a comma separated string.
        for dict_of_data in data_to_log:
            for key in dict_of_data:
                labels +=  f"{key}," 
        return labels
    
    def _get_values(data_to_log):
        """
        Takes in an array of dictionaries and returns a comma separated string of the values.
        
        Parameters
        ----------
        data_to_log : Array of dicts
            The dictionaries to be logged.  These should be in the same order they will be sent to the logger every time this will determine the order the columns are written.
                
        Returns
        -------
        values : string
            A comma separated string of the values from the provided dictionaries. 
        """
        values = ''
        # Go through all the dictionaries pulling all the values of each one into a comma separated string.
        for dict_of_data in data_to_log:
            for key in dict_of_data:
                values +=  f"{dict_of_data[key]},"    
        return values
       
    
if __name__ == '__main__':
    import time
    
    # Create some test dictonaries.
    data_1 = {
        'a' : 1,
        'b' : 2,
        'c' : False,
    }

    data_2 = {
        'd' : 3,
        'e' : 8,
    }

    data_3 = {
        'f' : False,
        'g' : 9.81,
    }

    data_full = [data_1, data_2, data_3]

    logger = DataLogger(data_full, path = 'test_folder', base_name = 'test', max_file_size = (2 * 10**3)) # max filesize = 2 kb to force second file
    
    # Write some data to check that it creates new files if it goes beyond the max filesize.  Change a value to track the number of lines and to make sure different values are being written.
    while data_1['a'] <= 100:
        logger.log(data_full)
        data_1['a'] += 1
        data_full = [data_1, data_2, data_3]
    # wait to make sure a new timestamp is used.
    time.sleep(1)
    # check to make sure new file sets are being created.
    logger.new(data_full, path = 'test_folder', base_name = 'new', max_file_size = (2 * 10**3))
    while data_1['a'] <= 150:
        logger.log(data_full)
        data_1['a'] += 1
        data_full = [data_1, data_2, data_3]
    
        