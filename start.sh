#!/usr/bin/env bash

echo Running crash-start script...

while true
	do /home/pi/reverb/env/bin/python3 /home/pi/reverb/reverb_rewrite.py && break
done