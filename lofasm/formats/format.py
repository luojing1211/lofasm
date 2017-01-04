"""
This is a module to register the lofasm file fomats.
"""
import ..bbx.bbx as bbx
import abc

class DataFormatMeta(abc.ABCMeta):
    """
    This is a Meta class for data formats registeration. In order ot get a format
    registered, a member called 'format_name' has to be in the DataFormat subclass
    """
    def __init__(cls, name, bases, dct):
        regname = '_format_list'
        if not hasattr(cls,regname):
            setattr(cls,regname,{})
        if 'format' in dct:
            getattr(cls,regname)[cls.format] = cls
        super(DataFormatMeta, cls).__init__(name, bases, dct)

class DataFormat(object):
    """
    This is a base class for different lofams data file formats
    """
    __metaclass__ = DataFormatMeta
    def __init__(self, format_cls):
        self.format_name = None
        self.format_cls = format_cls

    def instantiate_format_cls(self,):
        raise NotImplementedError

    def is_format(self, filename):
        raise NotImplementedError

    def read_header(self):
        raise NotImplementedError

    def read_data(self):
        raise NotImplementedError

    def write_header(self):
        raise NotImplementedError

    def write_data(self):
        raise NotImplementedError


class BBXFormat(DataFormat):
    format = 'bbx'
    def __init__(self,):
        super(BBXFormat, self).__init__(bbx.LofasmFile)
        self.format_name = 'bbx'
        self.format_instance = None
        self.instance_error = "Please instantiate the format class first using"
        self.instance_error += " '.instantiate_format_cls' method"
    def instantiate_format_cls(self, filename, verbose=False, mode='read', gz=None):
        """
        This is a wrapper function for instantiate bbx class. The description of
        parameters are given in ../bbx/bbx.py LofasmFile class docstring.
        BBX docstring
        -------------

        """
        self.format_instance = self.format_cls(filename, verbose=False, \
                                               mode='read', gz=None)
        self.__doc__ + = self.format_cls.__doc__
    def is_format(self, filename):
        return bbx.is_lofasm_bbx(filename)

    def read_header(self):
        if self.format_instance is None:
            raise AttributeError(self.instance_error)
        else:
            return self.instance_error.header

    def read_data(self, N=None):
        if self.format_instance is None:
            raise AttributeError(self.instance_error)
        else:
            self.format_instance.read_data(self, N=None)
            return self.format_instance.data