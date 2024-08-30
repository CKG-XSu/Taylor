import numpy as np
import pandas as pd
import xarray as xr
    

def create_monthly_mask(dates=['1982-01','2018-12']):
    """
    Takes a flat array of ungridded data and grids it to the
    grid of the given xr.DataArray.

    Parameters
    ----------
    dates : list of strings, default ['1982-01','2018-12']
        list of start and stop dates

    Returns
    -------
    xda : xr.DataArray
        a DataArray with time,lat,lon dimensions and all zeros
    """
    ### Define spatial
    lon = np.arange(0.5,360,1)
    lat = np.arange(-89.5,90,1)
    time = pd.date_range(start=f'{dates[0]}-01T00:00:00.000000000', 
                          end=f'{dates[1]}-01T00:00:00.000000000',
                          freq='MS')+ np.timedelta64(14, 'D')

    ### Create dataArray
    xda = xr.DataArray(np.zeros((len(time),len(lat), len(lon))), 
                          dims=['time','lat','lon'], 
                          coords=[time, lat, lon])
    return xda


def create_monthly_mask2(dates=['1982-01','2018-12']):
    """
    Takes a flat array of ungridded data and grids it to the
    grid of the given xr.DataArray.

    Parameters
    ----------
    dates : list of strings, default ['1982-01','2018-12']
        list of start and stop dates

    Returns
    -------
    xda : xr.DataArray
        a DataArray with time,lat,lon dimensions and all zeros
    """
    ### Define spatial
    lon = np.arange(-179.5,180,1)
    lat = np.arange(-89.5,90,1)
    time = pd.date_range(start=f'{dates[0]}-01T00:00:00.000000000', 
                          end=f'{dates[1]}-01T00:00:00.000000000',
                          freq='MS')+ np.timedelta64(14, 'D')

    ### Create dataArray
    xda = xr.DataArray(np.zeros((len(time),len(lat), len(lon))), 
                          dims=['time','lat','lon'], 
                          coords=[time, lat, lon])
    return xda

def match_ungridded_to_gridded(variable, time, lat, lon, xda):
    """
    Takes a flat array of ungridded data and grids it to the
    grid of the given xr.DataArray.

    Parameters
    ----------
    variable : array-like
        a flat array with the values you'd like to match to the DataArray
    time : array-like
        an increasing time array in datetime64 format
    lat : array-like
        an increasing array of latitude - does not have to be monotonic
    lon : array-like
        an increasing array of longitude - does not have to be monotonic
    xda : xr.DataArray
        the target gridded xr.DataArray that you would like to compare the
        values with. Must have time, lat and lon dimensions

    Returns
    -------
    xds : xr.Dataset
        a Dataset that has mean and std DataArrays matching the input DataArray.
        IF values is a pandas.Series the name from that variable will be used,
        otherwise `variable` will be prepended to the _mean and _std DataArrays.

    Reference
    ---------
    Gregor, L. and Lebehot, A. D. and Kok, S. and Scheel Monteiro, P. M. A. 2019.
        comparative assessment of the uncertainties of global surface-ocean CO2
        estimates using a machine learning ensemble (CSIR-ML6 version 2019a) --
        have we hit the wall? Geoscientific Model Development Discussions.
        DOI: 10.5194/gmd-2019-46

    """

    # check that coordinates are present
    for key in ['time', 'lat', 'lon']:
        assert key in xda.dims, '`{}` is not in the input DataArray'.format(
            key)

    assert all(xda.time.diff('time') > np.timedelta64(
        '0', 'D')), 'time is not strictly increasing'
    assert all(xda.lat.diff('lat') > 0), 'latitude is not strictly increasing'
    assert all(xda.lon.diff('lon') > 0), 'latitude is not strictly increasing'

    # check that time is in right format
    assert np.issubdtype(
        time, np.datetime64), 'time must be in datetime64 format'

    t = xda.time.values
    y = xda.lat.values
    x = xda.lon.values

    def make_bins(dim):
        delta = np.diff(dim) / 2
        bins = np.r_[
            dim[0] - delta[0],
            dim[1:] - delta,
            dim[-1] + delta[-1]]
        return bins

    # create bins to cut along
    tbins = make_bins(t)
    ybins = make_bins(y)
    xbins = make_bins(x)

    # cut returns the bins to which the time, lat and lon belong
    # we give the indicies of t, y, x as labels to use for indexing later
    tidx = pd.cut(np.array(time), tbins, labels=np.arange(t.size))
    yidx = pd.cut(np.array(lat),  ybins, labels=np.arange(y.size))
    xidx = pd.cut(np.array(lon),  xbins, labels=np.arange(x.size))

    # groupby bins and get mean and std
    df = (pd.Series(variable)
          .groupby([tidx, yidx, xidx])
          .agg(['mean', 'std'])
          .reset_index()
          .rename(columns={'level_0': 'it',
                           'level_1': 'iy',
                           'level_2': 'ix'}))
    # make the indicies as integers
    it, iy, ix = df[['it', 'iy', 'ix']].values.T.astype(int)

    # get the name if it exists
    name = getattr(variable, 'name', 'out')

    # make DataArrays for the mean and std
    # copy the input dataarray and make a copy - replace with nans
    xda1 = xda.copy() * np.nan
    xda2 = xda.copy() * np.nan
    xda1.name = name + '_mean'
    xda2.name = name + '_std'
    # merge into dataset
    xds = xr.merge([xda1, xda2])

    # take the values from the binned data and place into the dataArrays
    xds[xda1.name].values[it, iy, ix] = df['mean']
    xds[xda2.name].values[it, iy, ix] = df['std']

    return xds
