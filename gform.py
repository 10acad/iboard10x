from __future__ import print_function
import os, sys
import gspread
from oauth2client.service_account import ServiceAccountCredentials
#from oauth2client.service_account import SignedJwtAssertionCredentials
import pandas as pd
import json, os, sys
import ssm_credentials as ssm

user_email = 'yabebal@10academy.org'

def get_credentials(cr,path=None,isssm=False):
    SCOPE = ["https://spreadsheets.google.com/feeds"]
    #SCOPE = ["https://www.googleapis.com/auth/sqlservice.admin"]
    #if 
    if isssm:
        print('get_credentials:  SSM path passed...')
        cr = ssm.get_strings_ssm(cr)
        
    #print('get_credentials: type(cr)=',type(cr))
    
    if isinstance(cr,str):
        print('get_credentials:  string passed...')
        if path is None:
            home_dir = os.path.expanduser('~')
            credential_dir = os.path.join(home_dir, '.credentials')
        else:
            credential_dir=path
        
        SECRETS_FILE = os.path.join(credential_dir, cr)
        # Authenticate using the signed key
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(SECRETS_FILE, SCOPE)
        
    elif isinstance(cr,dict):
        print()
        print('get_credentials:  dict passed...')
        print('passing dict to gstream ServiceAccountCredentials.from_json_keyfile_dict with keys:')
        print(cr.keys())
        print()
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(cr, SCOPE)
        
    else:
        
        #may have been already instantiated 
        credentials = cr
    
    return credentials #.with_subject(useremail)

def gsheet2df(cr,sheeturl=None,name=None,path=None):
    #
    #get credential from file or dict
    credentials = get_credentials(cr,path=path)
    
    gc = gspread.authorize(credentials)

    if not sheeturl is None:
        workbook = gc.open_by_url(sheeturl)
        
    elif not name is None:
        workbook = gc.open(name)
        
    else:
        print("The following sheets are available")
        for sheet in gc.openall():
            print("{} - {}".format(sheet.title, sheet.id))
        workbook = gc.open(sheet.title)
    
        
        
    # Get the first sheet
    sheet = workbook.sheet1

    df = pd.DataFrame(sheet.get_all_records())

    return df


class gsheet_manager():
    def __init__(self,
                     ssm_path = "/oauth/google/gspread",
                     sheeturl='https://docs.google.com/spreadsheets/d/1dZc3ehRFeqjR0JriuCZtdfcgb9-sfgAC-i70Xj1LcR8/edit#gid=876627421'
                     ):
        self.sheet_url = sheeturl
        self.ssm_path = ssm_path
        
        print('reading credentials from %s: '%ssm_path)
        self.cr_dict = get_credentials(ssm_path,isssm=True)


    def get_applicants(self):
        dfsheet = gsheet2df(self.cr_dict,self.sheeturl)
        return self.sheet_remap(dfsheet)
        
    def sheet_remap(self,df):
        '''remap column headers, drop empty fields and set email as index '''
        #
        colmapper = dict(motivation='Why do you want to become a 10 Academy Fellow? (280 characters maximum!)',
                awards = 'Past awards, publications or scholarships',
                firstname = 'First Name',
                lastname = 'Last Name (Family Name or Surname)',
                country = 'Country (Passport)',
                email = 'Email address',
                gender = 'Gender',
                birthyear = 'Year of birth',
                experience = 'Your entrepreneurship experience',
                workexperience = 'Your work experience',
                whotoldyou = 'How did you hear about this opportunity'
                )
        #reverse dict
        colmapper = {v: k for k, v in colmapper.items()}
        #
        df = df.drop(['Email Address'],axis=1) #inplace
        df = df.rename(index=str, columns = colmapper).set_index('email')
        
        return df

if __name__=='__main__':
    #
    ssm_path = "/oauth/google/gspread"
    print('reading credentials from %s: '%ssm_path)    
    cr_dict = get_credentials(ssm_path,isssm=True)
    #
    print('Passing credential t gsheet2df ..')
    sheeturl='https://docs.google.com/spreadsheets/d/1dZc3ehRFeqjR0JriuCZtdfcgb9-sfgAC-i70Xj1LcR8/edit#gid=876627421'
    df = gsheet2df(cr_dict,sheeturl)
    #
    print('Data successfully obtained from google sheet!')
    #
    print('Form Data in Pandas')
    print('Number of rows: ',len(df))
    print(df.head())

