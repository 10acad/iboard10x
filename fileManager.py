import pandas as pd
import sys, os, glob
import datetime
import fnmatch #fnmatch.filter to match against a simple expression
import pickle
#
import utils as ut

def splitall(path):
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts

def get_date_from_filename(path):
    '''We assume path has a structure of the following
      /dir/y(year)/m(month)/prefix_d(day).ext
      '''
    allparts = splitall(path)
    l = len(allparts)
    tstr = ['d0','m0','y0']
    for i in range(3):
        if l>i:
            tstr[i] = allparts[l-(i+1)]


    dstr, mstr, ystr = tstr

    #get day
    try:
        d = int(dstr.split('.')[0].split('_')[1].split('d')[1])
    except:
        d = 1
        print('splitting day from %s failed'%dstr)

    #get month
    try:
        m = int(mstr.split('m')[1])
    except:
        m = 1
        print('splitting month from %s failed'%mstr)

    #get year
    try:
        y = int(ystr.split('y')[1])
    except:
        y = 1970
        print('splitting year from %s failed'%ystr)

    return datetime.date(y,m,d)


def _get_recent_file_from_filelist(filelist):

    filename = ''
    recent = datetime.date(1970,1,1)
    try:
        for f in filelist:
            date = get_date_from_filename(f)
            if date>recent:
                filename = f
                recent = date
    except:
        raise

    return filename, recent

def get_latest_filename(path,prefix,ext='*',verbose=0):
    '''
    we assume path has the following structure
    #path/y(year)/m(month)/prefix_d(day).ext

    Some wisdom for this function is obtained from
    https://stackoverflow.com/questions/2186525/how-to-use-glob-to-find-files-recursively
    '''

    try:
        p = os.path.join(path, '**/%s*%s'%(prefix,ext))
        filelist = glob.iglob(p, recursive=True)

        if verbose>1:
            print('iglob filelist for %s: '%p)
            print(filelist)
    except:
        raise
        filelist = []
        for root, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, '*%s*%s'%(prefix,ext)):
                filelist.append(os.path.join(root, filename))
        if verbose>1:
            print('os.walk based filelist: ')
            print(filelist)


    return _get_recent_file_from_filelist(filelist)

def make_latest_filename(rootdir, prefix, ext='', mkdir=True):
    '''
    This function can be called to construct filenames for analysis outputs.
    '''

    #get date component strings
    today = datetime.date.today()
    day = 'd%s'%today.day
    month = 'm%s'%today.month
    year = 'y%s'%today.year

    #make directories from year and month
    #join year
    path = os.path.join(rootdir,year)

    #join month
    path = os.path.join(path,month)

    #create dir if it doesn't exist
    if mkdir and (not os.path.exists(path)):
        os.makedirs(path)

    #join with filename
    if len(prefix)>1 and prefix[-1] != '_':
        prefix += '_'

    #check extension
    if len(ext)>0:
        if ext[0] != '.':
            ext = '.' + ext

    filename = prefix + day + ext
    path = os.path.join(path,filename)

    return path

def write_pkl_file(obj,filename):
    with open(filename, 'wb') as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return filename

def save_pkl_file(obj,filename):
    return write_pkl_file(obj,filename)

def read_pkl_file(filename):
    with open(filename, 'rb') as handle:
        obj = pickle.load(handle)

    return obj

class data_manager():
    def __init__(self,s3path=None):
        if s3path is None:
            thisdir = os.path.dirname(__file__)
            s3path = os.path.join(thisdir, 'data')