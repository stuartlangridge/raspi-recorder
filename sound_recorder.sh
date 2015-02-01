#!/bin/bash
amixer -c 1 cset numid=2 55,44
exec arecord -f S16_LE -D hw:1,0 -r 48000 \
    record-$(date -u +"%Y%m%dT%H%M%S").wav

