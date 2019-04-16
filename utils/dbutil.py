import psycopg2
import pandas as pd
import pandas.io.sql as psql
import sys, os
#
from sqlalchemy import create_engine
import sqlalchemy as sa
#
import queries as qq
import gform 

def config(filename='/var/www/moodle/config.php'):
    
    if not os.path.exists(filename):
        filename=os.path.basename(filename)

    #print('Config file is: '+filename)
    
    if not os.path.exists(filename):
        print('Config file does not exist: '+filename)
        raise
    
    # get section, default to postgresql
    gdict = {'$CFG->dbhost':'host',
             '$CFG->dbname':'database',
             '$CFG->dbuser':'user',
             '$CFG->dbpass':'password',
             '$CFG->prefix':'prefix'}
        
    dbparams = {}

    with open(filename) as f:
        for line in f:
            if line.startswith('$CFG->'):
                for s in ['\n',' ',';','"',"'"]: 
                    line = line.replace(s,'')
                    
                kv = line.split('=')
                if kv[0] in gdict.keys():
                    k = gdict[kv[0]]
                    v = kv[1] 
                    dbparams[k] = v

    #print('config_values',dbparams)
    
    if not dbparams:
        raise Exception('Config params  not found in {1} file'.format(filename))
    
    return dbparams


def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()
        prefix=params.pop('prefix')
        
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
 
        # create a cursor
        cur = conn.cursor()
        
        # execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')
 
        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)
       
     # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')

