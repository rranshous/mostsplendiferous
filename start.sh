#!/bin/bash
sudo su www-data -c "cd /home/robby/coding/mostsplendiferous; cherryd -d -c cherryconfig.production.ini -i cherryappd"
