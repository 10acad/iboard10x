#!/usr/bin/python
#
#Ref:
#  http://www.postgresqltutorial.com/postgresql-python/query/
#
import psycopg2
import pandas as pd
import pandas.io.sql as psql
import sys, os, glob
import datetime
import fnmatch #fnmatch.filter to match against a simple expression
#
from sqlalchemy import create_engine
import sqlalchemy as sa
#
import queries as qq
import gform
import ssm_credentials as ssm
from utils import  dbutil
import fileManager as fman
#from configparser import ConfigParser
import utils.log_analysis as logstat
from utils.logger import get_logger

cdir = os.path.dirname(__file__)
logger = get_logger('dbManager')

#today = datetime.today()
#datem = datetime(today.year, today.month, today.day)

class rds_manager():
    def __init__(self,verbose=1,datarootdir=os.path.join(cdir,'csvs'),connect=True):
        #
        self.verbose=verbose
        self.datarootdir = datarootdir

        # read connection parameters
        params = dbutil.config()
        #
        self.prefix = params.pop('prefix')
        self.db_params = params
        #
        self.cursorisopen = False  #if any 
        self.dbisopen = False
        #
        #dict to contain all tablenames that are read
        self.tablenames = {}

        #open connection
        if connect:
            self.engine = self.login()
    
    def login(self):
        return self.open_db_connection()
    
    def open_db_connection(self):
        # get connection to database
        try:
            proot = 'postgresql://{user}:{password}@{host}:5432/{database}'.format(**self.db_params)
            #print(proot)
            logger.info('Connecting to the PostgreSQL database...using sqlalchemy engine')
            engine = create_engine(proot)
            # connect to the PostgreSQL server
            #engine = psycopg2.connect(**self.db_params)    
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(error)

        self.dbisopen = True
        return engine

    def close_connection(self):
        if self.dbisopen:
            self.engine.close()
            self.dbisopen = False

    def close_cursor(self):
        if self.cursorisopen:
            self.cursor.close()
            self.cursorisopen = False
            
    def close(self):
        self.close_cursor()
        self.close_connection()

    def dbtest(self):
        query='SELECT version()'

        print('PostgreSQL database version:')
        print(self.get_data(q=query))

    def get_cursor(self,query):
        # create a new cursor
        cur = self.engine.cursor()
        #excute a new query
        cur.execute(query)
        
        return cur
    
    def open_cursor(self,query,verbose=None):
        #
        if verbose is None:
            verbose=self.verbose
            
        # create a cursor for general use
        self.cursor = self.get_cursor(query)
        nrow = self.cursor.rowcount
        
        #set flag
        self.cursorisopen = True
        #display info
        if verbose>0:
            print("Query:")
            print(query)
            print("result number of rows: ", nrow)        

        return nrow
        
    def get_data_from_cursor(self,cur=None,nrow=0,**kwargs):
        #check cur is passed or there exists open cursor
        if cur is None:
            if self.iscursoropen:
                cur = self.cursor
            else:
                print('WARNING: no open cursor is found, setting result to []')
                return res
                
        # display the PostgreSQL database server version
        if nrow==1:
            #The  fetchone() fetches the next row in the result set.
            #It returns a single tuple or None when no more row is available.
            res = cur.fetchone()
        elif nrow>1:
            #The  fetchmany(size=cursor.arraysize) fetches the next set of rows
            #specified by the size parameter. If you omit this parameter, the
            #arraysize will determine the number of rows to be fetched.
            #The  fetchmany() method returns a list of tuples or an empty list if
            #no more rows available.
            res = cur.fetchmany(nrow)
        else:
            #The  fetchall() fetches all rows in the result set and returns a list of tuples.
            #If there are no rows to fetch, the  fetchall() method returns an empty list.
            res = cur.fetchall()

        return res

    def get_data(self,q=None,nrow=0,table=True,**kwargs):
        '''
        note q can be a table name
        Ref: 
           http://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql
        Options:
          **kargs can have the pandas options
          parse_dates=['Date'] - explicitly force columns to be parsed as dates
          parse_dates={'Date': '%Y-%m-%d'}
          index_col='id' - the name of the column as the DataFrame index
          columns=['Col_1', 'Col_2'] -  specify a subset of columns to be read
        '''
        if q is None:
            if self.cursorisopen:
                self.get_data_from_cursor(nrow=nrow)
            else:
                print('WARNING: Cursor is not open and no query is passed.')
                res = []
        else:
            #get data by doing database query
            if table:
                res = psql.read_sql(q, self.engine,**kwargs)
            else:
                res = psql.read_sql_table(q, self.engine,**kwargs)                
            #cur = self.get_cursor(q)
            #res = self.get_data_from_cursor(cur=cur, nrow=nrow)
            #cur.close()
            
        return res
    
    def dict_to_df(self, query_result,date=True):
        items = {
            val: dict(query_result["records"][val])
            for val in range(query_result["totalSize"])
            }
        df = pd.DataFrame.from_dict(items, orient="index").drop(["attributes"], axis=1)
        
        if date: # date indicates if the df contains datetime column
            df["CreatedDate"] = pd.to_datetime(df["CreatedDate"], format="%Y-%m-%d") # convert to datetime
            df["CreatedDate"] = df["CreatedDate"].dt.strftime('%Y-%m-%d') # reset string
        return df

    #------------ READ DATA FROM FILE ------------
    def read_latest_users(self,verbose=0):
        ff, date = fman.get_latest_filename(self.datarootdir,'users',ext='csv',verbose=verbose-1)
        logger.debug('user_csv_filename: %s and date=%s'%(ff,date))
        date_columns = ['timecreated','firstaccess','lastaccess',
                        'lastlogin','currentlogin','ApplicationDate']
        if verbose>1:
            logger.debug('reading the latest users file from: %s'%ff)

        df = pd.read_csv(ff,index_col='id',parse_dates=date_columns)

        return df

    def read_latest_log_summary(self,verbose=0):
        date_columns = ['TotalTimeSpent','MeanLoginTime']
        dmapper = {'ActivitiesCount': int,
                   'TotalSecondsSpent':int,
                   'LoginCount':int}

        ff, date = fman.get_latest_filename(self.datarootdir,'logsummary',ext='csv',verbose=0)

        if verbose>1:
            logger.debug('reading the latest logsummary file from: %s'%ff)

        df = pd.read_csv(ff, index_col = 'UserId',dtype=dmapper)

        return df

    #------------ FETCH DATA FROM DATABASE ------------

    def fetch_moodle_users(self,tablename='mdl_user'):
        self.tablenames['user'] = tablename
        #define params and mappings
        index='id'
        date_columns = ['timecreated','firstaccess','lastaccess','lastlogin','currentlogin']
        columns = ['confirmed','username','firstname','lastname','email','country','picture']
        columns.extend(date_columns)

        #read table
        return self.get_data(tablename,columns=columns, index_col=index,parse_dates=date_columns)

    def make_user_fullname(self,dfu):
        fullname = dfu[['firstname', 'lastname']].apply(lambda x: ' '.join(x), axis=1)
        df_fullname = pd.concat([fullname, dfu['email']],axis=1).sort_index()
        return df_fullname.rename(index=str,columns={0:'fullname'})

    def fetch_lastaccess(self,tablename='mdl_user_lastaccess'):
        self.tablenames['lastaccess'] = tablename
        index='userid'
        date_columns = ['timeaccess']

        #read table
        return db.get_data(tablename, index_col=index,parse_dates=date_columns)

    def fetch_courses(self,tablename='mdl_course'):
        self.tablenames['course'] = 'mdl_course'
        return db.get_data('mdl_course',columns=['id', 'category','shortname','fullname','format','visible'])
    
    def fetch_accounts(self):
        query_text = "SELECT Id, Name FROM Account"
        try:
            query_result = self.engine.query(query_text)
        except SalesforceExpiredSession as e:
            self.login()
            query_result = self.engine.query(query_text)

        accounts = self.dict_to_df(query_result,False)
        return accounts


    def add_case(self, query):
        try:
            self.engine.Case.create(query)
        except SalerdsorceExpiredSession as e:
            self.login()
            self.engine.Case.create(query)
        return 0


if __name__ == '__main__':
    #
    #params = config()            
    #connect() 
    
    db = rds_manager(verbose=0)

    res = db.engine.table_names()
    print('===============================')
    print([x for x in res if 'log' in x  ])
    print('===============================')
    
    q = qq.count_mdl_course
    q = qq.quiz_submission_by_hrday
    q = qq.monthly_usage_stat
    q = qq.moodle_usage_summary
    q = qq.list_db_tables
    q = "SELECT * FROM mdl_logstore_standard_log"

   
    res=db.get_data(q)
    

    print('===============================')
    print('query: {}'.format(q))
    print('===============================')
    print()
    print('type (result): ',type(res))
    print(res.describe())
    print(res.iloc[0])
