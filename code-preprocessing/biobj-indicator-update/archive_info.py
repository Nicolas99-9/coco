# -*- coding: utf-8 -*-
"""Classes containing information about COCO archive files.
"""
import os

from .exceptions import PreprocessingWarning, PreprocessingError
import load_data as ld

class ProblemInstanceInfo:
    """Contains information on the problem instance: suite_name, function, 
       dimension, instance and a list of file names with archived solutions for
       this problem instance.
    """
    
    def __init__(self, file_name, suite_name, function, dimension, instance):
        """Instantiates a ProblemInstanceInfo object.
        """
        self.suite_name = suite_name
        self.function = function
        self.dimension = dimension
        self.instance = instance
        self.file_names = [file_name]
        
        self.current_file_initialized = False
        self.current_position = 0
        self.current_file_index = 0
        
    def __str__(self):
        result = "{}_f{:02d}_i{:02d}_d{:02d}".format(self.suite_name, 
                                                     self.function,
                                                     self.instance,
                                                     self.dimension)
        return result
    
    def add_file_name(self, file_name):
        """Adds file_name to the list of file names of self.
        """
        self.file_names.append(file_name)
        
    def equals_problem(self, suite_name, function, dimension):
        """Returns true if self has the same suite_name, 
           function and dimension as the given ones and false otherwise.
        """
        if (self.suite_name != suite_name):
            return False
        if (self.function != function):
            return False
        if (self.dimension != dimension):
            return False
        return True
        
    def equals(self, suite_name, function, dimension, instance):
        """Returns true if this self has the same suite_name, function, 
           dimension and instance as the given ones and false otherwise.
        """
        if (not self.equals_problem(suite_name, function, dimension)):
            return False
        if (self.instance != instance):
            return False
        return True       
        
    def fill_archive(self, archive):
        """Reads the solutions from the files and feeds them to the given 
           archive. 
        """
        # Make sure this works also for the last line in the file!
        
        for file_name in self.file_names:            
            with open(file_name, 'r') as f:
            
                instance_found = False
                stop_reading = False
                
                for line in f:
                    if (line[0] == '%') and stop_reading:
                        break
                    elif ((line[0] == '%') and (not instance_found)):
                        if ("instance" in line):
                            value = ld.get_key_value(line[1:], "instance")
                            if (int(value) == self.instance):
                                instance_found = True
                    elif instance_found:
                        if (line[0] != '%'):
                            if not stop_reading:
                                stop_reading = True
                            # Solution found, feed it to the archive
                            archive.add_solution(line.split('\t')[1], 
                                                 line.split('\t')[2], 
                                                 line)
                     
                f.close()
                if not instance_found:
                    raise PreprocessingError("File '{}' does not contain "
                    "'instance = {}'".format(file_name, self.instance))   
    
    def write_archive_solutions(self, output_path, archive):
        """Appends solutions to a file in the output_path named according
           to self's suite_name, function and dimension.
        """
        ld.create_path(output_path)
        file_name = os.path.join(output_path, 
                                 "{}_f{:02d}_d{:02d}_nondominated.adat".format(
                                     self.suite_name,
                                     self.function, 
                                     self.dimension))
                                     
        with open(file_name, 'a') as f:
            f.write("% instance = {}\n%\n".format(self.instance))
            
            while True:
                text = archive.get_next_solution_text()
                if text is None:
                    break
                
                f.write(text)
            
            f.close()

class ArchiveInfo:
    """Collects information on the problem instances contained in all archives.
    """
    
    def __init__(self, input_path):
        """Instantiates an ArchiveInfo object.
           
           Extracts information from all archives found in the input_path and 
           returns the resulting ArchiveInfo instance.
        """
        
        self.problem_instances = []
        self.current_instance = 0
        count = 0
        
        # Read the information on the archive
        input_files = ld.get_file_name_list(input_path)
        if (len(input_files) == 0):
            raise PreprocessingError("Folder '{}' does not exist or is "
            "empty".format(input_path))
        
        archive_info_list = []
        for input_file in input_files:
            try:
                archive_info_set = ld.get_archive_file_info(input_file)
            # If any problems are encountered, the file is skipped 
            except PreprocessingWarning as warning:
                print(warning)
            else:
                archive_info_list.append(archive_info_set)
                count += 1
                
        print("Successfully processed archive information from {} files.".format(count))
        
        # Store archive information
        print("Storing archive information...")
        for archive_info_set in archive_info_list:
            for archive_info_entry in archive_info_set:
                self._add_entry(*archive_info_entry)
        
    def __str__(self):
        result = ""
        for instance in self.problem_instances:
            if instance is not None:
                result += str(instance) + "\n"
        return result
        
    def _add_entry(self, file_name, suite_name, function, dimension, instance):
        """Adds a new ProblemInstanceInfo instance with the given suite_name, 
           function, dimension, instance to the list of problem instances if
           an instance with these exact values does not exist yet. If it already
           exists, the current file_name is added to its list of file names.
        """
        found = False
        for problem_instance in self.problem_instances:
            if (problem_instance.equals(suite_name, function, dimension, instance)):
                problem_instance.add_file_name(file_name)
                found = True
                break
        
        if not found:
            self.problem_instances.append(ProblemInstanceInfo(file_name, 
                                                              suite_name, 
                                                              function, 
                                                              dimension, 
                                                              instance))        
                                                             
    def get_next_problem_instance_info(self):
        """Returns the current ProblemInstanceInfo and increases the counter. 
           If there are no more instances left, returns None.        
        """
        if (self.current_instance >= len(self.problem_instances)):
            return None
        
        self.current_instance += 1
        return self.problem_instances[self.current_instance - 1]