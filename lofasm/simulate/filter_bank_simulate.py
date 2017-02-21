import numpy as np
from ..bbx.bbx import LofasmFile as lfbbx


def get_info_bbx(self, bbx_cls):
    """
    This is function the get all the necessary information from bbx file.
    """
    hdr = bbx_cls.header
    info = {}
    info['num_time_bin'] = int(hdr['dim1_len'])
    info['time_resolution'] = float(hdr['dim1_span'])/info['num_time_bin']
    info['num_freq_bin'] = int(hdr['dim2_len'])
    info['freq_resolution'] = float(hdr['dim2_span'])/info['num_freq_bin']
    freq_off_set_DC = float(hdr['frequency_offset_DC'].split()[0])
    info['freq_start'] = float(hdr['dim2_start']) + freq_off_set_DC)
    time_off_J2000 = float(hdr['time_offset_J2000'].split()[0])
    info['time_start'] = float(hdr['dim1_start']) + time_off_J2000
    info['time_end'] = info['time_start'] + float(hdr['dim1_span'])
    info['freq_end'] = info['freq_start'] + float(hdr['dim2_span'])
    info['time_axis'] = np.arange(info['time_start'], info['time_end'], info['time_resolution'])
    info['freq_axis'] = np.arange(info['freq_start'], info['freq_end'], info['freq_resolution'])
    return info

FILETYPE = {'bbx': (lfbbx, get_info_bbx)}

class FilterBank(object):
    """
    This is a class for holding filter bank data.
    A filter bank data is a two dimesion array.
    dim 1 (x-axis) : time
    dim 2 (y-axis) : frequency
    dim 3          : power. undefined unit
    """
    def __init__(self, name, from_file=False, time_reslt=0.0,  num_time_bin=0, \
                 freq_reslt=0.0, num_freq_bin=0, freq_start=0.0, time_start=0.0,\
                 data_gen=None, gap_filling=None, filename=None, filetype=None):
        self.name = name
        self.info = {self.name:{},}
        self.time_resolution = time_reslt
        self.num_time_bin = num_time_bin
        self.freq_resolution = freq_reslt
        self.num_freq_bin = num_freq_bin
        self.freq_start = freq_start
        self.time_start = time_start
        self.time_end = time_start + time_reslt * num_time_bin
        self.freq_end = freq_start + freq_reslt * num_freq_bin
        self.time_axis = np.arange(self.time_start, self.time_end, time_reslt)
        self.freq_axis = np.arange(self.freq_start, self.freq_end, freq_reslt)
        self.data = np.zeros((self.num_time_bin, self.num_freq_bin))
        self.data_gen = data_gen

        if from_file:
            if filetype is None or filename is None:
                raise ValueError('Please provide file name and file type to'
                                 ' input data from a file.')
            self.read_from_file(filename, filetype)
        if gap_filling is None:
            self.gap_fill_fun = self.gap_fill_default

    @property
    def time_start(self):
        return self._time_start
    @time_start.setter
    def time_start(self, value):
        self._time_start = value
        self.info[self.name]['time_start'] = value

    @property
    def time_end(self):
        return self._time_end
    @time_end.setter
    def time_end(self, value):
        self._time_end = value
        self.info[self.name]['time_end'] = value

    @property
    def freq_start(self):
        return self._freq_start
    @freq_start.setter
    def freq_start(self, value):
        self._freq_start = value
        self.info[self.name]['freq_start'] = value

    @property
    def freq_end(self):
        return self._freq_end
    @freq_end.setter
    def freq_end(self, value):
        self._freq_end = value
        self.info[self.name]['freq_end'] = value

    def __add__(self, other):
        """
        Define the operator for adding two filter bank data together.
        """
        if self.time_resolution != other.time_resolution:
            raise ValueError('Can only add two filter bank data with the same'
                             ' time resolution.')
        if self.freq_resolution != other.freq_resolution:
            raise ValueError('Can only add two filter bank data with the same'
                             ' frequency resolution.')

        if not np.array_equal(self.freq_axis, other.freq):
            raise ValueError('Can only add two filter bank data with the same
                             'freq range.')
        # Check time range.
        time_range = np.array([self.time_start, self.time_end, other.time_start, \
                               other.time_end])
        # find the min and max time
        new_start = time_range.min()
        new_end = time_range.max()
        new_time_bin = (new_end - new_start)/self.time_resolution
        new_flt_data = FilterBank('total', self.time_resolution, new_time_bin,\
                                  self.freq_resolution, self.num_freq_bin, \
                                  self.freq_start, new_start)
        new_start_idx = np.array([0,0])
        for st in [self.time_start, other.time_start]:
            new_start_idx[0] = np.abs(st - new_flt_data.time_axis).argmin()
        new_end_idx = new_start_idx + np.array([self.num_time_bin, other.num_time_bin])
        # prevent index over flow.
        excd = np.where(new_end_idx >= new_flt_data.num_time_bin)[0]
        new_start_idx[excd] -= 1
        new_flt_data.data[new_start_idx[0]:new_end_idx[0], :] += self.data
        new_flt_data.data[new_start_idx[1]:new_end_idx[1], :] += other.data
        # Check gap
        diff = np.array([new_start_idx[0] - new_start_idx[1], \
                         new_end_idx[0] - new_end_idx[1]], \
                         new_end_idx[0] - new_start_idx[1], \
                         new_start_idx[0] - new_end_idx[1])
        if np.all(np.greater(diff, [0,0,0,0])):
            new_flt_data.info[new_flt_data.name]['gap'] = new_start_idx[0] - new_end_idx[1]
        elif np.all(np.less(diff, [0,0,0,0])):
            new_flt_data.info[new_flt_data.name]['gap'] = new_start_idx[1] - new_end_idx[0]
        new_flt_data.info.updata(self.info)
        new_flt_data.info.updata(other.info)
        return new_flt_data

    def __neg__(self,):
        new_flt_data = FilterBank('neg_' + self.name, self.time_resolution, self.num_time_bin,\
                                  self.freq_resolution, self.num_freq_bin, \
                                  self.freq_start, self.time_start)
        new_flt_data.data /= -1
        return new_flt_data

    def __sub__(self, other):
        self.__add__(other.__neg__())

    def __isub__(self, other):
        """
        Define the operator for adding two filter bank data together.
        """
        if self.time_resolution != other.time_resolution:
            raise ValueError('Can only add two filter bank data with the same'
                             ' time resolution.')
        if self.freq_resolution != other.freq_resolution:
            raise ValueError('Can only add two filter bank data with the same'
                             ' frequency resolution.')

        if not np.array_equal(self.freq_axis, other.freq):
            raise ValueError('Can only add two filter bank data with the same
                             'freq range.')
        # Check time range.
        time_range = np.array([self.time_start, self.time_end, other.time_start, \
                               other.time_end])
        # find the min and max time
        new_start = time_range.min()
        new_end = time_range.max()
        new_time_bin = (new_end - new_start)/self.time_resolution
        if new_start == self.time_start and new_end == self.time_end:
            self.data += other.data
        else:
            # resize time axis
            self.time_axis = np.arange(new_start, new_end, self.time_resolution)
            # resize data
            tempo = np.zeros((new_time_bin, self.num_freq_bin))
            new_start_idx = np.array([0,0])
            for st in [self.time_start, other.time_start]:
                new_start_idx[0] = np.abs(st - new_flt_data.time_axis).argmin()
            new_end_idx = new_start_idx + np.array([self.num_time_bin, other.num_time_bin])
            # prevent index over flow.
            excd = np.where(new_end_idx >= new_flt_data.num_time_bin)[0]
            new_start_idx[excd] -= 1
            temp[new_start_idx[0]:new_end_idx[0], :] += self.data
            temp[new_start_idx[1]:new_end_idx[1], :] += other.data
            # Check gap
            diff = np.array([new_start_idx[0] - new_start_idx[1], \
                         new_end_idx[0] - new_end_idx[1]], \
                         new_end_idx[0] - new_start_idx[1], \
                         new_start_idx[0] - new_end_idx[1])
            if np.all(np.greater(diff, [0,0,0,0])):
                self.info[self.name]['gap'] = new_start_idx[0] - new_end_idx[1]
            elif np.all(np.less(diff, [0,0,0,0])):
                self.info[self.name]['gap'] = new_start_idx[1] - new_end_idx[0]
        self.time_start = new_start
        self.time_end = new_end
        self.num_time_bin = new_time_bin
        self.info.updata(other.info)
        return self

    def generate_data(self, **kws):
        return self.data_gen(self.data, **kws)

    def gap_fill_default(self, gap):
        """
        This a function that determine what to fill into the filter bank data
        gap.
        """
        gap = np.zeros(gap.shape)
        return gap

    def get_info_from_file(self, filecls, filetype):
        info = FILETYPE[filetype][1](filecls)
        for k in info.keys():
            setter(self, k, info[k])


    def read_from_file(self, filename, filetype):
        """
        This function is to read a filter bank data from a file.
        Parameter
        ---------
        filename: str
            The file name to be read in.
        type: str
            The type of the file. It will map to a file class from FILETYPE dict.
        """
        df = FILETYPE[filetype][0](filename)
        self.get_info_from_file(df, filetype)
        self.data = df.data


    def write(self, filename, filetype, gz=True):
        filecls = FILETYPE[filetype][0](filename, mode='write', gz=gz)
        filecls.add_data(self.data)
        hdr = {}
        hdr['dim1_span'] = self.time_end - self.time_start
        hdr['dim2_span'] = self.freq_end - self.freq_start
        hdr['dim1_start'] = self.time_start
        hdr['dim2_start'] = self.freq_start
        for k, v in hdr.items():
            filecls.set(k, v)
        filecls.write()
        filecls.close()