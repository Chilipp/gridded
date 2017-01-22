#!/usr/binenv python

# py2/3 compatibility
from __future__ import absolute_import, division, print_function, unicode_literals

import netCDF4 as nc4
import numpy as np

from datetime import datetime, timedelta

from .utilities import get_dataset

# import collections
# from collections import OrderedDict


class EnvProp(object):

    def __init__(self,
                 name=None,
                 units=None,
                 time=None,
                 data=None,
                 **kwargs):
        '''
        A class that represents a natural phenomenon and provides an interface to get
        the value of the phenomenon at a position in space and time. EnvProp is the base
        class, and returns only a single value regardless of the time.

        :param name: Name
        :param units: Units
        :param time: Time axis of the data
        :param data: Value of the property
        :type name: string
        :type units: string
        :type time: [] of datetime.datetime, netCDF4.Variable, or Time object
        :type data: netCDF4.Variable or numpy.array
        '''

        self.name = self._units = self._time = self._data = None

        self.name = name
        self.units = units
        self.data = data
        self.time = time
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return ('{0.__class__.__module__}.{0.__class__.__name__}('
                'name="{0.name}", '
                'time="{0.time}", '
                'units="{0.units}", '
                'data="{0.data}", '
                ')').format(self)

    '''
    Subclasses should override\add any attribute property function getter/setters as needed
    '''

#     @property
#     def data(self):
#         '''
#         Underlying data
#
#         :rtype: netCDF4.Variable or numpy.array
#         '''
#         return self._data

    @property
    def units(self):
        '''
        Units of underlying data

        :rtype: string
        '''
        return self._units

    @units.setter
    def units(self, unit):
#         if unit is not None:
#             if not unit_conversion.is_supported(unit):
#                 raise ValueError('Units of {0} are not supported'.format(unit))
        self._units = unit

    @property
    def time(self):
        '''
        Time axis of data

        :rtype: gnome.environment.property.Time
        '''
        return self._time

    @time.setter
    def time(self, t):
        if t is None:
            self._time = None
        elif isinstance(t, Time):
            self._time = t
        elif isinstance(t, collections.Iterable):
            self._time = Time(t)
        else:
            raise ValueError("Object being assigned must be an iterable or a Time object")

    def at(self, *args, **kwargs):
        '''
        Find the value of the property at positions P at time T

        :param points: Coordinates to be queried (P)
        :param time: The time at which to query these points (T)
        :param time: Specifies the time level of the variable
        :param units: units the values will be returned in (or converted to)
        :param extrapolate: if True, extrapolation will be supported
        :type points: Nx2 array of double
        :type time: datetime.datetime object
        :type time: integer
        :type units: string such as ('m/s', 'knots', etc)
        :type extrapolate: boolean (True or False)
        :return: returns a Nx1 array of interpolated values
        :rtype: double
        '''

        raise NotImplementedError()

#     def in_units(self, unit):
#         '''
#         Returns a full cpy of this property in the units specified.
#         WARNING: This will cpy the data of the original property!
#
#         :param units: Units to convert to
#         :type units: string
#         :return: Copy of self converted to new units
#         :rtype: Same as self
#         '''
#         cpy = copy.copy(self)
#         if hasattr(cpy.data, '__mul__'):
#             cpy.data = unit_conversion.convert(cpy.units, unit, cpy.data)
#         else:
#             warnings.warn('Data was not converted to new units and was not copied because it does not support multiplication')
#         cpy._units = unit
#         return cpy


class VectorProp(object):

    def __init__(self,
                 name=None,
                 units=None,
                 time=None,
                 variables=None,
                 **kwargs):
        '''
        A class that represents a vector natural phenomenon and provides an interface to get the value of
        the phenomenon at a position in space and time. VectorProp is the base class

        :param name: Name of the Property
        :param units: Unit of the underlying data
        :param time: Time axis of the data
        :param variables: component data arrays
        :type name: string
        :type units: string
        :type time: [] of datetime.datetime, netCDF4.Variable, or Time object
        :type variables: [] of EnvProp or numpy.array (Max len=2)
        '''

        self.name = self._units = self._time = self._variables = None

        self.name = name

        if all([isinstance(v, EnvProp) for v in variables]):
            if time is not None and not isinstance(time, Time):
                time = Time(time)
            units = variables[0].units if units is None else units
            time = variables[0].time if time is None else time
        if units is None:
            units = variables[0].units
        self._units = units
        if variables is None or len(variables) < 2:
            raise ValueError('Variables must be an array-like of 2 or more Property objects')
        self.variables = variables
        self._time = time
        unused_args = kwargs.keys() if kwargs is not None else None
        if len(unused_args) > 0:
#             print(unused_args)
            kwargs = {}
        super(VectorProp, self).__init__(**kwargs)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return ('{0.__class__.__module__}.{0.__class__.__name__}('
                'name="{0.name}", '
                'time="{0.time}", '
                'units="{0.units}", '
                'variables="{0.variables}", '
                ')').format(self)

    @property
    def time(self):
        '''
        Time axis of data

        :rtype: gnome.environment.property.Time
        '''
        return self._time

    @property
    def units(self):
        '''
        Units of underlying data

        :rtype: string
        '''
        if hasattr(self._units, '__iter__'):
            if len(set(self._units) > 1):
                return self._units
            else:
                return self._units[0]
        else:
            return self._units

    @units.setter
    def units(self, unit):
        self._units = unit
        if self.variables is not None:
            for v in self.variables:
                v.units = unit

    @property
    def varnames(self):
        '''
        Names of underlying variables

        :rtype: [] of strings
        '''
        return [v.varname if hasattr(v, 'varname') else v.name for v in self.variables ]

    def _check_consistency(self):
        '''
        Checks that the attributes of each GriddedProp in varlist are the same as the GridVectorProp
        '''
        raise NotImplementedError()

    def at(self, *args, **kwargs):
        '''
        Find the value of the property at positions P at time T

        :param points: Coordinates to be queried (P)
        :param time: The time at which to query these points (T)
        :param time: Specifies the time level of the variable
        :param units: units the values will be returned in (or converted to)
        :param extrapolate: if True, extrapolation will be supported
        :type points: Nx2 array of double
        :type time: datetime.datetime object
        :type time: integer
        :type units: string such as ('m/s', 'knots', etc)
        :type extrapolate: boolean (True or False)
        :return: returns a Nx2 array of interpolated values
        :rtype: double
        '''
        return np.column_stack([var.at(*args, **kwargs) for var in self.variables])


class Time(object):
    _const_time = None

    def __init__(self,
                 time=None,
                 filename=None,
                 varname=None,
                 tz_offset=None,
                 offset=None,
                 **kwargs):
        '''
        Representation of a time axis. Provides interpolation alphas and indexing.

        :param time: Ascending list of times to use
        :param tz_offset: offset to compensate for time zone shifts
        :type time: netCDF4.Variable or [] of datetime.datetime
        :type tz_offset: datetime.timedelta

        '''
        if isinstance(time, (nc4.Variable, nc4._netCDF4._Variable)):
            self.time = nc4.num2date(time[:], units=time.units)
        else:
            self.time = time

        self.filename = filename
        self.varname = varname

#         if self.filename is None:
#             self.filename = self.id + '_time.txt'

        if tz_offset is not None:
            self.time += tz_offset

        if not self._timeseries_is_ascending(self.time):
            raise ValueError("Time sequence is not ascending")
        if self._has_duplicates(self.time):
            raise ValueError("Time sequence has duplicate entries")

        self.name = time.name if hasattr(time, 'name') else None

    @classmethod
    def from_netCDF(cls,
                    filename=None,
                    dataset=None,
                    varname=None,
                    datavar=None,
                    tz_offset=None,
                    **kwargs):
        if dataset is None:
            dataset = get_dataset(filename)
        if datavar is not None:
            if hasattr(datavar, 'time') and datavar.time in dataset.dimensions.keys():
                varname = datavar.time
            else:
                varname = datavar.dimensions[0] if 'time' in datavar.dimensions[0] else None
                if varname is None:
                    return None
        time = cls(time=dataset[varname],
                   filename=filename,
                   varname=varname,
                   tz_offset=tz_offset,
                   **kwargs
                       )
        return time

    @staticmethod
    def constant_time():
        if Time._const_time is None:
            Time._const_time = Time([datetime.now()])
        return Time._const_time

    @property
    def data(self):
        if self.filename is None:
            return self.time
        else:
            return None

    def __len__(self):
        return len(self.time)

    def __iter__(self):
        return self.time.__iter__()

    def __eq__(self, other):
        r = self.time == other.time
        return all(r) if hasattr(r, '__len__') else r

    def __ne__(self, other):
        return not self.__eq__(other)

    def _timeseries_is_ascending(self, ts):
        return all(np.sort(ts) == ts)

    def _has_duplicates(self, time):
        return len(np.unique(time)) != len(time) and len(time) != 1

    @property
    def min_time(self):
        '''
        First time in series

        :rtype: datetime.datetime
        '''
        return self.time[0]

    @property
    def max_time(self):
        '''
        Last time in series

        :rtype: datetime.datetime
        '''
        return self.time[-1]

    def get_time_array(self):
        return self.time[:]

    def time_in_bounds(self, time):
        '''
        Checks if time provided is within the bounds represented by this object.

        :param time: time to be queried
        :type time: datetime.datetime
        :rtype: boolean
        '''
        return not time < self.min_time or time > self.max_time

    def valid_time(self, time):
        if time < self.min_time or time > self.max_time:
            raise ValueError('time specified ({0}) is not within the bounds of the time ({1} to {2})'.format(
                time.strftime('%c'), self.min_time.strftime('%c'), self.max_time.strftime('%c')))

    def index_of(self, time, extrapolate=False):
        '''
        Returns the index of the provided time with respect to the time intervals in the file.

        :param time: Time to be queried
        :param extrapolate:
        :type time: datetime.datetime
        :type extrapolate: boolean
        :return: index of first time before specified time
        :rtype: integer
        '''
        if not (extrapolate or len(self.time) == 1):
            self.valid_time(time)
        index = np.searchsorted(self.time, time)
        return index

    def interp_alpha(self, time, extrapolate=False):
        '''
        Returns interpolation alpha for the specified time

        :param time: Time to be queried
        :param extrapolate:
        :type time: datetime.datetime
        :type extrapolate: boolean
        :return: interpolation alpha
        :rtype: double (0 <= r <= 1)
        '''
        if not len(self.time) == 1 or not extrapolate:
            self.valid_time(time)
        i0 = self.index_of(time, extrapolate)
        if i0 > len(self.time) - 1:
            return 1
        if i0 == 0:
            return 0
        t0 = self.time[i0 - 1]
        t1 = self.time[i0]
        return (time - t0).total_seconds() / (t1 - t0).total_seconds()

