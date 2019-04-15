import boto3
import json, sys, os


def put_strings_ssm(fjson,ssm_path=None, private='private'):
    #
    with open(fjson, "r") as read_file:
        data = json.load(read_file)

    #construct ssm path
    ssm_path = '/%s/%s'%('oauth',os.path.basename(fjson))
    if len(params)>2:
        ssm_path=params[2]
    #    
    print('ssm_path=%s'%ssm_path)

    #start boto processing
    client = boto3.client('ssm')

    for k,v in data.items():
        #use securestring only for variables with name containing private
        #t = None
        t='String'
        
        if 'client_secret'==k or 'client_id'==k or private in k:
            t='SecureString'
        #elif 'client_id'==k or 'client_email'==k or 'project_id'==k:
        #    t='String'
    
        if not t is None:        
            try:
                print('ssm putting: t=%s, key=%s'%(t,os.path.join(ssm_path,k)))
                client.put_parameter(Name=os.path.join(ssm_path,k),
                                Value=v,
                                Type=t,
                                Overwrite=True) #keyid=''
            except:
                print('** Failed to put: t=%s, key=%s'%(t,os.path.join(ssm_path,k)))
    #
    return ssm_path

def get_strings_ssm(ssm_path):
    #start boto processing
    client = boto3.client('ssm')
    
    #test how we are going to access    
    response = client.get_parameters_by_path(
        Path=ssm_path,
        Recursive=True,
        WithDecryption=True,    
        # ParameterFilters=[
        #     {
        #         'Key': 'string',
        #         'Option': 'string',
        #         'Values': 'string',
        #     },
        # ],
        #MaxResults=123,
        #NextToken='string'
        )['Parameters']

    return { os.path.basename(x['Name']):x['Value'] for x in response }

if __name__=='__main__':
    params = sys.argv
    name = params[0]
    print(params)

    if len(params)<2:
        print('Usage: %s /path/filename.json'%name)

    #
    fjson = params[1]
    #save credential 
    ssm_path = put_strings_ssm(fjson,ssm_path=None, private='private')

    #get credential
    res=get_strings_ssm(ssm_path)
    print('****** Retrived *****')
    print(res)
    print()
