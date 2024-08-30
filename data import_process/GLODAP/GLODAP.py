#***************************************************************************************************************
# This is a module for processing GLODAP data
# 
# the functions TqdmUpTo, get_GLODAP are coutesy of:
#   https://github.com/oscarbranson/cbsyst/blob/master/cbsyst/test_data/GLODAP_data/get_GLODAP_data.py
#***************************************************************************************************************

import numpy as np
import pandas as pd
import os
import zipfile
import urllib.request as ureq
from tqdm import tqdm
import cbsyst as cb

#********************************************
### TqdmUpTo : progress bar
#********************************************
class TqdmUpTo(tqdm):
    """Provides `update_to(n)` which uses `tqdm.update(delta_n)`."""
    def update_to(self, b=1, bsize=1, tsize=None):
        """
        b  : int, optional
            Number of blocks transferred so far [default: 1].
        bsize  : int, optional
            Size of each block (in tqdm units) [default: 1].
        tsize  : int, optional
            Total size (in tqdm units). If [default: None] remains unchanged.
        """
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)  # will also set self.n = b * bsize


#********************************************
### get_GLODAP : download function
#********************************************
def get_GLODAP(leave_zip=True):
    """
    Downloads GLODAP data and saves a file named GLODAPv2_pH_DIC_ALK_subset.csv
    in your current directory

    Parameters
    ----------
    dates : list of strings, default ['1982-01','2018-12']
        list of start and stop dates

    Returns
    -------
    () : 
    """
    if not os.path.exists('./GLODAPv2 Merged Master File.csv.zip'):
        print('Fetching GLODAPv2 Data (Olsen et al, 2016)...')

        ### URL to GLODAP zip file
        GLODAP_url = 'http://cdiac.ornl.gov/ftp/oceans/GLODAPv2/Data_Products/data_product/GLODAPv2%20Merged%20Master%20File.csv.zip'

        ### download GLODAP data
        with TqdmUpTo(unit='B', unit_scale=True, miniters=1,
                      desc='Downloading GLODAPv2') as t:
            ureq.urlretrieve(GLODAP_url, './GLODAPv2 Merged Master File.csv.zip',
                             reporthook=t.update_to)

        # ### open URL
        # file = requests.get(GLODAP_url, stream=True)
        # total_size = int(file.headers.get('content-length', 0))

        # # Download data
        # with open('./GLODAPv2 Merged Master File.csv.zip', 'wb') as f:
        #     for data in tqdm(file.iter_content(1024), total=total_size / (1024), unit='KB', unit_scale=True):
        #         f.write(data)
    else:
        print('Found GLODAPv2 Data (Olsen et al, 2016)...')

    print('Reading data...')
    ### open zip
    zf = zipfile.ZipFile('./GLODAPv2 Merged Master File.csv.zip')

    ### read data into pandas
    gd = pd.read_csv(zf.open('GLODAPv2 Merged Master File.csv'))

    ### replace missing values with nan
    gd.replace(-9999, np.nan, inplace=True)

    print("Selecting 'good' (flag == 2) data...")
    ### isolate good data only (flag = 2)
    # gd.loc[gd.phts25p0f != 2, 'phts25p0'] = np.nan
    gd.loc[gd.phtsinsitutpf != 2, 'phtsinsitutp'] = np.nan
    gd.loc[gd.tco2f != 2, 'tco2'] = np.nan
    gd.loc[gd.talkf != 2, 'talk'] = np.nan
    gd.loc[gd.salinityf != 2, 'salinity'] = np.nan
    gd.loc[gd.phosphatef != 2, 'phosphate'] = np.nan
    gd.loc[gd.silicatef != 2, 'silicate'] = np.nan

    ### Identify rows where ph, dic, talk and sal are present
    # phind = ~gd.phtsinsitutp.isnull()
    # dicind = ~gd.tco2.isnull()
    # alkind = ~gd.talk.isnull()
    # salind = ~gd.salinity.isnull()

    gd.dropna(subset=['phtsinsitutp', 'tco2', 'talk', 'temperature', 'salinity',
                      'pressure', 'silicate', 'phosphate'], inplace=True)

    print('Saving data subset...')
    ### Isolate those data
    # gds = gd.loc[phind & dicind & alkind & salind, ['phts25p0', 'phtsinsitutp', 'tco2', 'talk', 'temperature', 'salinity',
    #                                                 'cruise', 'station', 'cast', 'year', 'month', 'day', 'hour',
    #                                                 'latitude', 'longitude', 'bottomdepth', 'maxsampdepth', 'bottle',
    #                                                 'pressure', 'depth', 'theta', 'silicate', 'phosphate']]
    gds = gd.loc[:, ['phts25p0', 'phtsinsitutp', 'tco2', 'talk', 'temperature', 'salinity',
                     'cruise', 'station', 'cast', 'year', 'month', 'day', 'hour',
                     'latitude', 'longitude', 'bottomdepth', 'maxsampdepth', 'bottle',
                     'pressure', 'depth', 'theta', 'silicate', 'phosphate']]

    ### Save the datasubset
    gds.to_csv('./GLODAPv2_pH_DIC_ALK_subset.csv', index=False)

    ### boolean if you want to save the zip file
    if not leave_zip:
        os.remove('./GLODAPv2 Merged Master File.csv.zip')

    return



#********************************************
### process_GLODAP : cleans the data
#********************************************
def process_GLODAP(fl='./GLODAPv2_pH_DIC_ALK_subset.csv', surface_depth=20):
    ### Reads GLODAP data
    gd = pd.read_csv(fl)

    ### *************************************************************
    ### exclude is weird date in cruise cruise 270
    ### April 31 makes no sense. I suspect this should be May 1st
    ### should I trust this entire cruise?
    ### *************************************************************
    ### Drops the non-existent date April 31st. 
    gd = gd.drop(gd[(gd.month==4) & (gd.day==31)].index)
    ### Drops the entire cruise 270, the cruise with eroneous date
    #gd = gd.loc[gd.cruise != 270]

    ### Put year/month/day/hour into sensible format
    gd['date'] = pd.to_datetime(gd[['year', 'month', 'day', 'hour']])

    ### drop NaNs in subset
    gd.dropna(subset=['phtsinsitutp', 'temperature',
                      'salinity', 'tco2', 'talk',
                      'pressure', 'phosphate', 'silicate'], inplace=True)

    ### Convert from -180 / 180 to 0/360 longitude
    def f(row):
        if row['longitude'] < 0:
            val = row['longitude'] + 360
        else:
            val = row['longitude']
        return val

    ### Apply function to dataframe 
    gd['lon_0360'] = gd.apply(f, axis=1)

    ### convert pressure to bar
    gd.pressure /= 10 

    ### Calculate pCO2 using cbsyst
    ### This also incorporates the calcluated pCO2 
    ### into the dataframe and then picks out only the necessary variables
    calc_pco2 = cb.Csys(pH=gd.phtsinsitutp, 
                     DIC=gd.tco2, 
                     T=gd.temperature, 
                     S=gd.salinity, 
                     P=gd.pressure, 
                     TP=gd.phosphate, 
                     TSi=gd.silicate, 
                     BT=415.7)

    ### put pCO2 into GLODAP dataframe - gd
    gd['pco2'] = calc_pco2.pCO2

    ### Groupby profile and take index where depth is min
    gd = gd.loc[gd.groupby(['cruise','station','cast'])['depth'].idxmin()]

    ### Set index to dates
    gd_sub = gd.loc[:, ['date', 'latitude', 'lon_0360', 'depth', 'pco2']].rename(columns={'latitude':'lat',
                                                                                          'lon_0360':'lon',
                                                                                          'pco2':'spco2',
                                                                                          'date':'time'}).set_index(['time'])

    ### Only look in top 20 meters
    gd_sub = gd_sub.where(gd_sub['depth']<=surface_depth).dropna()
    #len(gd_sub.where(gd_sub['depth']<=20).dropna())
    
    return gd_sub