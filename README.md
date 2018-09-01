# pragoPi
Pragotron watch driver with Raspberry Pi

![PJ 27](https://raw.githubusercontent.com/dorsic/pragoPi/master/images/IMG_1502.JPG)

### Description
Pragotron slave watch is moved by a magnetic coil feed by alternating impulses. Based on the watch these should be between +-24V up to +-60V. Each minute an impulse of length between 1000-2000 ms is generated by the master clock with opposite polarity than the previous one.

To simulate the master clock a Raspberry Pi Zero W is used with time sychronized by ntpd. A cron like scheduler issues an impulse on the beginning of each minute on pin 23 or 24. This impulse drives L393 motor driver module and connects the upscaled voltage to the clock.

## Used Parts
- Pragotron slave watch
- Raspberry Pi Zero W
- L393 driver
- DC-DC voltage upscaler

- Raspberry Pi power adapter
- Raspberry Pi power cable
- 8GB Class 10 microSDHC card

## Raspberry Pi Preparation
Flash the OS with etcher. In my case the Raspbian Strech Lite from 06-27-2018 was used.
Copy ssh file and wpasupplicant.config

Insert the card to RPi and boot.

Find out the RPi IP address. Use `netscan` or any other method.
Consider to fix the IP address of you Raspberry Pi on the router using a static IP.

### Configure the OS
`sudo raspi-config`
- change hostname
- change password

##### Update the system
```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get dist-upgrade
```

##### Install NTPD
Installation the Network Time Protocol deamon to synchronize the system time with internet time servers.
```
sudo apt-get install ntp
```

You can check with `ntpq -c pe` command if time servers where found. After a while that server with an `*` is the primary server to which is the time synchronized.

### Install the App

##### Install GIT-Core
```
sudo apt-get install git-core
```

##### Install Pip3
```
sudo apt-get install python3-pip
```

##### Install Required Modules (Python3)
- RPi-GPIO
```
sudo apt-get install python3-rpi.gpio
```

- APscheduler
```
sudo pip3 install apscheduler (3.5.1)
```

- Flask
```
sudo pip3 install flask (1.0.2)
```

##### Clone the repository
```
cd ~
git clone https://github.com/dorsic/pragoPi
```

##### Test the App
```
cd ~/pragoPi
sudo python3 app.py
```

Issue a http get request from another computer or console
```
curl -XGET http://pragopi:80/impulse
curl -XGET http://pragopi:80/setTime/2132
```


##### Install System Service
```
sudo cp pragopi.service /lib/systemd/system 
sudo chmod 644 /lib/systemd/system/pragopi.service
chmod +x /home/pi/pragoPi/app.py
sudo systemctl daemon-reload
sudo systemctl enable pragopi.service
sudo systemctl start pragopi.service
```

### API
Move clock one minute forward
`curl -XGET http://pragopi:80/impulse`
Set time
`curl -XGET http://pragopi:80/setTime/<displayedTime>`
where *displayedTime* is the current time showed by the clock in HHMM format. Both 12 and 24 hour times are supported.

## Wiring
Wire PIN 23 a 24 to motor driver
and then the VDD.

