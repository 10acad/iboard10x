import sys

sys.path.append("/var/www/flask")
sys.path.append("/var/www/flask/iboard10x")

#Working with Virtual Environments
#Ref: http://flask.pocoo.org/docs/1.0/deploying/mod_wsgi/
#activate virtualenv

python_home = "/var/www/dashenv"
activate_this = python_home + '/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))
    
from index import server as application 


