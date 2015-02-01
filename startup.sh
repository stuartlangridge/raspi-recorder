#!/bin/bash
cd $(dirname $0)
source venv/bin/activate
supervisord -c ./supervisor.conf

