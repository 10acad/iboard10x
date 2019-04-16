
from dbManager import *
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly
        
#get counts for action verbs
def get_logdf_count(df,verb='loggedin',dfjoin=None,dropid=[0,2,3,5]):
    df1 = df[dflog['action']==verb].groupby('userid').count()['id'].sort_values(ascending=False).to_frame()
    df1.rename(index=str,columns={'id':verb+'count'},inplace=True)
    
    droplist = []
    for x in dropid:
        y = str(x) 
        if y in df1.index:
            droplist.append(y)
    #print('droplist: ',droplist)
    if droplist:
        df1 = df1.drop(droplist, axis=0)    
    
    
    if not dfjoin is None:
        idx = [str(x) for x in df1.index.to_list()]
        dfx = dfjoin.loc[idx].copy()    
        dfx[verb+'count'] = df1        
        return dfx
        
        
    return df1

def user_dedication_per_login(df_user_in,
                              verbose=0,
                              infilter = dict(eventname=['user_login_failed','notification']),
                              equalfilter = dict(action=['failed','loggedout'])):
    '''
        Purpose:
        Compute time between login and last activity. 

        To be improved:
        (1) Right now we assume a uniform dedication time between login and last activity.
        For future we can improve the dedication time by considering an approperiate weight 
        which reflects which activities the person did, upweighting read & write cruds, and 
        removing idle times, for example a user viewed a dashboard and didn't do anything 
        for 20mins afterwards. 

        Note:
        - 12 April 2019 - first implementation by Y. Fantaye

    '''
    
    #define output variables
    dt = {'logintime':[], 
          'timespent':[],
          'timespent_seconds':[],
          'deltalogin':[],
          'nactivities':[]
         }        
    tot_dedication_time = 0

    
    #** Filter -- remove failed login/email/etc from user logs 
    mask = None
    for k,vlist in infilter.items():
        for v in vlist:
            if verbose>0: print('applying infilter verb=%s, val=%s: '%(k,v) )
            m = df_user_in[k].map(lambda x: not v in x)
            if mask is None:
                mask = m
            else:
                mask = mask & m
    
    #for all filter with ==
    for k,v in equalfilter.items():
        if verbose>0: print('applying equalfilter verb=%s, val=%s: '%(k,v))
        m = df_user_in[k].map(lambda x: x != v)
        #m = df_user_in[k].map(lambda x:x.strip()) != v
        mask = mask & m
    
    # applied the combined filters 
    df_user = df_user_in[mask].copy()

    #if no activity after filter return empty
    if len(df_user)<1:
        if verbose>0: 
            print('Current user does not have any activity after filtering out the following:')
            print('  * ')
        df = pd.DataFrame.from_dict(dt)
        df = df.set_index('logintime')
        return df, tot_dedication_time 
        
        
    #set index to timecreated
    df_user.index = df_user['timecreated'].map(lambda x:pd.to_datetime(x,unit='s'))

    #sort dataframe by index/time
    df_user = df_user.sort_index()

    #get sorted user login times
    login_times = df_user[df_user['action']=='loggedin'].index

    #tfmt = "%Y-%m-%d %H:%M:%S"
    tfmt = "%I:%M:%S%p"

    if verbose>0:
        print('****** user log counts before and after filtering: ',len(df_user_in), len(df_user))
        print('***** logedin times *****')
        print(login_times)
        print('**************************')    


    #get the oldest login
    time_prev_login = login_times[0]

    for time_next_login in login_times[1:]:
        #consequetive login time difference
        tlogin_diff = time_next_login-time_prev_login
        
        if verbose>0:                    
            s = 'time_prev_login=%s, time_next_login=%s, hrs_after_prev_login=%s'
            print( s%(time_prev_login, time_next_login, tlogin_diff ) )

        #filter the activities of the current login                        
        mask = (df_user.index >= time_prev_login) & (df_user.index < time_next_login) 

        #basend on filter, get last activity and the maximum time
        last_activity = df_user[mask]
        
        if len(last_activity)>1:
            time_last_activity = last_activity.index.max()

            #calculate time difference. If timecreated is in unix time, unit is in seconds
            tdiff = time_last_activity - time_prev_login
            tdiff_seconds = tdiff.seconds
            #
            tot_dedication_time += tdiff_seconds
            
            if verbose>0:
                print('** ----- #activities = %s, Dedicatin time = %s -----'%(len(last_activity),tdiff) )
                if tdiff.total_seconds()>36000:
                    print('--------exceptional login activity with ---------')
                    print('-------------------------------------------------')            
                    print(last_activity[['eventname','crud']])
                    print('')            
        else:            
            tdiff = 0
            tdiff_seconds = 0
            
        #output variables
        dt['logintime'].append(time_prev_login)
        dt['timespent'].append(tdiff)
        dt['timespent_seconds'].append(tdiff_seconds),
        dt['deltalogin'].append(tlogin_diff)
        dt['nactivities'].append(len(last_activity))


        #set previous login to current login time
        time_prev_login = time_next_login
        
    df = pd.DataFrame.from_dict(dt)
    df = df.set_index('logintime')
    summary = {'LoginCount':len(df),'TotalTimeSpent':df['timespent'].sum(),
               'ActivitiesCount':df['nactivities'].sum(),'MeanLoginTime':df['deltalogin'].mean()}
    return df, tot_dedication_time,summary
  
    
def dedication_per_user(dfgrp,verbose=0):
    tottime = {}
    dfstat = {}
    sstat = {x:[] for x in ['UserId','LoginCount','TotalTimeSpent','ActivitiesCount','MeanLoginTime']}
    
    for userid, df_user in dfgrp:
        if userid>0 and not userid in [0,1,2,3,4]:
            if len(df_user)>0:
                df,tuser,summary = user_dedication_per_login(df_user,verbose=verbose)
            else:
                df,tuser = None,0
            # 
            sstat[userid] = userid
            for k,v in summary.items():
                sstat[k].append(v)
            #
            tottime[userid] = tuser
            dfstat[userid] = df

            if verbose>0 and userid%30 == 0:
                print('iloop=%s, userid=%s, total dedication time=%s'%(i,userid, tuser))
    
    dfsummary = pd.DataFrame.from_dict(sstat)
    dfsummary = dfsummary.set_index('UserId')
    return dfstat, pd.Series(tottime),dfsummary

    
class mdl_log_analytics():
    def __init__(self,
                q="SELECT * FROM mdl_logstore_standard_log",
                dfid='id',
                grpid='userid',
                mkgrp=True,
                verbose=0
                ):
        
        #read log table
        self.verbose = verbose
        self.q = q
        self.dfid = dfid
        self.grpid = grpid
        
        #read log and make group
        self.dflog,self.dfloggrp = self.read_log_table(mkgrp=mkgrp)
        
        self.columns = self.dflog.columns
        
    def read_log_table(self,mkgrp=False):
        # #read log table
        dflog = db.get_data(self.q, 
                    index_col=self.index,
                    parse_dates=['timecreated'])
        
        #return groupby object if mkgrp is passed
        dfloggrp = None
        if mkgrp:
            dfloggrp = self.make_group(df=dflog)
            
            
        return dflog,dfloggrp
        
    def make_group(self,df=None,grpid=None):
        #
        grpid = self.grpid if grpid is None else grpid
        dflog = self.dflog if df is None else df
        #
        dfloggrp = dflog[dflog['action']==verb].groupby(grpid)
        return dfloggrp
    
    def check_log_grp(self):
        #make group if not available
        if self.dfloggrp is None:
            self.dfloggrp = self.make_group()
        
    def get_verb_count(self,dfgrp=None,
                       verb='loggedin',
                       dfjoin=None,
                       dropid=[0,2,3,5]):
        
        #default is use already grouped dataframe
        if dfgrp is None:
            self.check_log_grp()
            dfgrp = self.dfloggrp
        
        
        col = self.columns[0]
        df1 = dfgrp.count()[col].sort_values(ascending=False).to_frame()
        df1.rename(index=str,columns={col:verb+'count'},inplace=True)

        droplist = []
        for x in dropid:
            y = str(x) 
            if y in df1.index:
                droplist.append(y)
        #print('droplist: ',droplist)
        if droplist:
            df1 = df1.drop(droplist, axis=0)    


        if not dfjoin is None:
            idx = [str(x) for x in df1.index.to_list()]
            dfx = dfjoin.loc[idx].copy()    
            dfx[verb+'count'] = df1        
            return dfx


        return df1 

    def action_counts(self,verbose=None, 
                      verbs=None, 
                      dfjoin=None):
        #
        verbose = self.verbose if verbose is None else verbose
        if verbs is None:
            verbs = ['loggedin','viewed','answered','attempted','abandoned']
        
        
        df_action = {}
        total_action_count = {}
        for verb in verbs:
            try:
                df = get_logdf_count(dflog,verb=verb,dfjoin=df_fullname)
                if verbose>0:
                    print('----------- top 5 users with highest action=%s ----'%verb)
                    print(df.head())
                    print('--------------------------------------------------------')
                df_action[verb] = df
                total_action_count[verb] = len(df)
            except:
                if verbose>0:
                    print('***** failed to excute verb=%s *** '%verb)


    def timestamp_pretty_print(self,t):
        tc = t.components
        s = ''
        if tc.days>0:
            s += '%s.i2'%tc.day
        if tc.hours>0:
            s += '%s.i2'%t.hours
        if t.minutes>0:
            s += '%s.i2'%tc.minutes
        if t.secnds>0:
            s += '%s.i2'%tc.seconds        

        return s

    
    def dedication_per_user(self,dfgrp=None,verbose=0):
        #default is use already grouped dataframe
        if dfgrp is None:
            self.check_log_grp()
            dfgrp = self.dfloggrp
            
        tottime = {}
        dfstat = {}
        i=0
        for userid, df_user in dfgrp:
            if userid>0 and not userid in [0,1,2,3,4]:
                if len(df_user)>0:
                    df,tuser = user_dedication_per_login(df_user,verbose=verbose)
                else:
                    df,tuser = None,0

                tottime[userid] = tuser
                dfstat[userid] = df

                if verbose>0 and i%30 == 0:
                    print('iloop=%s, userid=%s, total dedication time=%s'%(i,userid, tuser))
            
        return dfstat, pd.Series(tottime)

    def plot_dedication_time(self,df):

        init_notebook_mode(connected=True)

        iplot(
            {
            "data": 
                [{
                    "x":df.index, 
                    "y":df.map(lambda x:float(x)/3600.0),
                }],

             "layout": 
                {
                    "xaxis": {'title':'UserID'},
                    "yaxis":{'title':'Dedication Time (Hrs)'},
                    "title":'Total Dedication Time Over 2 Months'
                },          
              }, 
            filename='total-dedication-time-per-user')
