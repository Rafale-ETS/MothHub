#!/bin/bash

sudo hcitool lecc --random CB:2C:0B:F3:5C:CC
sudo hcitool ledc 64
sudo hcitool ledc 65

sudo /home/pi/MothHub/.env/bin/python3 /home/pi/MothHub/MothHub.py -v
