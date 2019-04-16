#!/usr/bin/env bash

#guide from (in order of relevance)
# - https://www.digitalocean.com/community/tutorials/how-to-run-django-with-mod_wsgi-and-apache-with-a-virtualenv-python-environment-on-a-debian-vps
# - https://pypi.org/project/mod_wsgi/
# - https://optimalbi.com/blog/2016/03/31/apache-meet-python-flask/
# - https://blog.heptanalytics.com/2018/08/07/flask-plotly-dashboard/ 

dashdir="/var/www/dashenv"
#dashdir="${HOME}/pydash"
flaskdir="/var/www/flask"
projdir="iboard10x"

if [ ! -e $flashdir ]; then
    mkdir $flaskdir
fi

#dashdir is created later 
#if [ ! -e $dashdir ]; then
#   mkdir $dashdir
#fi

function apt_install_packages(){
    sudo apt-get update
    
    #install psycopg2
    sudo apt-get install postgresql libpq-dev postgresql-client postgresql-client-common
    pip install psycopg2
    
}

#
function make_apache_conf() {
    echo "----------- copy apache conf, ensite, and restart ..."
    #configure apache
    
    #*** install wsgi compiles with the same version as the virtualenv
    #*** the best method is to install it via pip
    #sudo apt-get install libapache2-mod-wsgi
    sudo pip3 install mod_wsgi

    #following this https://pypi.org/project/mod_wsgi/
    #add the out put of the mod_wsgi-express install-module to wsgi.load 
    v=`sudo mod_wsgi-express install-module | grep 'LoadModule wsgi_module'`
    echo "adding the following to apache wsgi.load mod:"
    echo "****  $v"
    echo $v > /etc/apache2/mods-available/wsgi.load
    sudo a2enmod wsgi #enable mod
    
    #if [ ! -z /etc/apache2/sites-available/flask.conf ]; then
    sudo cp $HOME/scripts/flask.conf /etc/apache2/sites-available/flask.conf
    sudo a2ensite flask
    sudo service apache2 restart    
    #fi
}

function install_pip_req() {
    source $dashdir/bin/activate
    apt_install_packages   #install some files pip fill fail  using apt 
    pip install -r $flaskdir/${projdir}/requirements.txt
}

function make_pyenv() {
    echo "------------- install virtualenv, create dir .."
    #install more 
    sudo apt-get install virtualenv
    #sudo apt install virtualenvwrapper
    sudo apt autoremove
    
    #set venv params
    if [ ! -z "${WORKON_HOME}" ]; then    
	echo "source /usr/share/virtualenvwrapper/virtualenvwrapper.sh" >> ~/.bashrc
	echo "export WORKON_HOME=~/.virtualenvs" >> ~/.bashrc
	echo "export PIP_VIRTUALENV_BASE=${WORKON_HOME}" >> ~/.bashrc    
	source ~/.bashrc
	mkdir ${WORKON_HOME}
    fi
    
    #create and activate pyenv
    echo "creating virtualenv dir .."
    envdir=`dirname $dashdir`
    envname=`basename $dashdir`
    if [ ! -d $dashdir ]; then	
	cd $envdir
	virtualenv $envname -p python3
    fi

}

function enable_pyenv(){
    echo "------------- activating virtualenv dir.."
    #getin to the right dir
    cd $dashdir
    source ${dashdir}/bin/activate
    
    echo "in dir `pwd`: installing packages .."
    #Installing Dependancies
    pip install -U pip
    pip install flask
    pip install plotly
    pip install pandas #will need it to manipulate the data
    pip install numpy
}
#-----------------------------------------
#---------done with setup ---
#-----------------------------------------

cd $flaskdir

#--------------------------
function make_test () {

    echo "writing webtool.py"
    #create webtool
    tee ${flaskdir}/webtool.py <<EOF #> /dev/null
from flask import Flask
 
app = Flask(__name__)
 
@app.route("/")
def hello():
 return "Hello world!"
 
if __name__ == "__main__":
    app.run()

EOF

    
    echo "writing webtool.wsgi"
    #create wsgi
    tee ${flaskdir}/webtool.wsgi <<EOF #> /dev/null

import sys

sys.path.append(${flaskdir})
sys.path.append(${flaskdir}/${projdir})

#Working with Virtual Environments
#Ref: http://flask.pocoo.org/docs/1.0/deploying/mod_wsgi/
#activate virtualenv

python_home = $dashdir
activate_this = python_home + '/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))
    
from index import server as application 


EOF

}



echo "writing test flast files "
echo "pwd: `pwd`"


make_apache_conf
make_pyenv
enable_pyenv
install_pip_req
make_test



#change permission
sudo chown -R www-data:www-data $flaskdir
sudo chmod -R 777 $flaskdir

#sudo chown -R www-data:www-data $dashdir
#sudo chmod -R 777 $dashdir

