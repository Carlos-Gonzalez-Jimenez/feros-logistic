#!/bin/bash

#echo "Corriendo migraciones..."
#python manage.py migrate
#
exec supervisord -c /etc/supervisor/conf.d/supervisor.conf