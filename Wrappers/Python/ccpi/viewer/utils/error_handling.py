import warnings

# See examples/error_observer.py for an example of using the ErrorObserver
# and EndObserver.


class ErrorObserver:

    def __init__(self, callback_fn=print):
        '''
        Parameters:
        -----------
        callback_fn : function, default print
            is called when an error occurs. It acts on the error message (str)
            so must be a function that takes a string as a parameter.
        '''
        self.__error_occurred = False
        self.__get_error_message = None
        self.CallDataType = 'string0'
        self.callback_fn = callback_fn

    def __call__(self, obj, event, message):
        self.__error_occurred = True
        self.__get_error_message = message
        self.callback_fn(self.__get_error_message)

    def error_occurred(self):
        occ = self.__error_occurred
        self.__error_occurred = False
        return occ

    def get_error_message(self):
        return self.__get_error_message


class EndObserver:
    ''' Occurs when the observed Algorithm finishes
    '''

    def __init__(self, error_observer, callback_fn):
        '''
        Parameters
        ----------
        error_observer: ErrorObserver
            the error observer attached to the object the EndObserver is attached to
        callback_fn: function
            function to run if an error hasn't been identified by the error_observer'''
        self.callback_fn = callback_fn
        self.error_observer = error_observer
        self.CallDataType = 'string0'

    def __call__(self, obj, event):
        if not self.error_observer.error_occurred():
            self.callback_fn()


# Format warning messages:
def customise_warnings():
    # prints warning message in bold yellow, file name and line number
    # without customising, warning message is printed twice, and is not
    # as clear
    def custom_warning_format(message, category, filename, lineno, line=None):
        return "{1}:{2}: \033[1;33;40m {1}: {0} \033[0m \n ".format(message, category.__name__, filename, lineno)

    warnings.formatwarning = custom_warning_format
