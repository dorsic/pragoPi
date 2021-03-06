# pragoPi
Pragotron watch driver with Raspberry Pi

![PJ 27](https://raw.githubusercontent.com/dorsic/pragoPi/master/images/IMG_1502.JPG)

### Description
Pragotron slave watches were used in offices, schools, train stations all around Czechoslovakia and the states behind Iron Curtain. Model PJ 27 (on the picture above) from the 60s is made from bakelite but newer steel model from 80s can be found also on [eBay](https://www.ebay.co.uk/sch/i.html?_from=R40&_trksid=p2380057.m570.l1313.TR3.TRC1.A0.H0.Xpragotron.TRS0&_nkw=pragotron&_sacat=0). The Pragotron clock is moved by a magnetic coil feed with alternating impulses. Based on the watch these impulses can be between +-24V to +-60V. Each minute an impulse of length between 1000-2000 ms is generated by the master clock with opposite polarity than the previous one. This impulse applied on the coil in the movement moves the watch one minute forward.

To simulate the master clock a Raspberry Pi (RPi) is used with time synchronized by ntpd. A cron like scheduler issues an impulse on the beginning of each minute on pin 23 and 24. The L298 motor driver is used to allow altering higher voltage impulses polarization. Output of the module is connected to the clock terminals.

A simple web interface implemented using python Flask is used to set up the current time when needed and Linux service is created to start the application automatically after boot.

L298 IO drives some small silent current also when control signals from RPi pins 23 and 24 are low. 2000ms impulse length is just a fraction of entire minute, so we can keep the module off for majority of time (58s out of 60s) with usage of the switching transistor.

I prefer to use the Raspberry Pi Zero W because of its small factor, WiFi and price, but you can also use RPi2B or RPi3, which do not require soldering.

## Used Parts
- Pragotron slave watch
- Raspberry Pi Zero W
- L298 motor driver
- DC-DC voltage upscaler
- optionally one general purpose transistor (e.g. 2N2222) and 1k Ohm resistor
- Raspberry Pi power adapter
- Raspberry Pi power cable
- 4GB Class 10 microSDHC card or bigger

![Used Parts](https://raw.githubusercontent.com/dorsic/pragoPi/master/images/IMG_1535.jpg)

## Raspberry Pi Preparation
*(A brief description, for detailed instructions follow [Setting up your Raspberry Pi](https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up). If you have no keyboard and monitor like me, search for RPi headless installation.)*

Flash the operating system to SD card with Etcher. In my case I used the Raspbian Stretch Lite from 06-27-2018.
For headless setup without monitor and keyboard copy an empty file named `ssh` to the \boot partition of the SD card and `wpasupplicant.config` file with you WiFi configuration to allow your Raspberry Pi to connect to your network and log in via ssh.

Insert the SD card to RPi and boot.

Find out the RPi IP address. Use `netscan` or check your router or any other method to find out.
Consider to fix the IP address of you RPi on the router using a static IP settings.

Log in to you Rasbperry Pi via ssh. The default Raspbian password for *pi* user is *raspberry*.

```ssh pi@<RPI IP address>```

### Prepare the Raspberry Pi Operating System
*(Condensed version of [Finishing the setup](https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up/6).)*

Once logged in to you RPi I recommend to do some basic setup with `raspi-config`.
Issue 
```sudo raspi-config```
command and change the password and hostname (e.g. *pragoPi* as in my case) and set the country and time zone.

Next update you system with
```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get dist-upgrade
```

##### Install NTPD
*(An optional but highly recommended step.)*

Using Network Time Protocol (NTP) is an easy way how to keep time on your RPi accurate. NTP servers are connected to GNSS or other accurate time sources (even primary time and frequency standards) and broadcast the time information to clients. NTP daemon witch runs in your RPi listens to this messages, computes the network delay, jitter and the corrections of frequency of the RPi oscillator to provide more accurate time information.

To install NTP daemon run following command
```
sudo apt-get install ntp
```
After a while, you can check with `ntpq -c pe` command if time servers where found. 
A server with an asterisk `*` is the primary server to which is the time of your RPi synchronized.
This is how the output may look like
```
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
 0.debian.pool.n .POOL.          16 p    -   64    0    0.000    0.000   0.002
 1.debian.pool.n .POOL.          16 p    -   64    0    0.000    0.000   0.002
 2.debian.pool.n .POOL.          16 p    -   64    0    0.000    0.000   0.002
 3.debian.pool.n .POOL.          16 p    -   64    0    0.000    0.000   0.002
+www.thr.sk      147.231.2.6      2 u  553 1024  377   15.036   -1.132  75.498
*cn10v1.christ-n 217.31.202.100   2 u  772 1024  377   15.148   -2.111   6.322
-95-105-193-228. 93.184.71.155    3 u  848 1024  377   19.133    6.851   3.832
+safi.initipi.sk 195.146.149.222  2 u  620 1024  377   26.503    1.262   7.782
-server.antechne 194.57.169.1     3 u  574 1024  377   15.989    0.608  13.697
+185.28.102.19 ( 124.216.164.14   2 u  691 1024  377   22.945    1.860   8.826
```

## Wiring

![Wiring Diagram](https://raw.githubusercontent.com/dorsic/pragoPi/master/images/wiring.png)

##### Connecting the DC-DC upscaler
Connect RPi PIN 4 (5V) to voltage upscaler input pin marked with sign (+) and the RPi PIN 6 (GND) to the upscaler input pin marked with sign (-).

##### Connecting the L298 motor driver
Remove the 12V jumper. Will supply 24V to our clock which is more than 12V. According to the module specification, we need to also supply separate 5V input voltage to the pin 6. 
Remove the motor 2 enable jumper (ENB) and leave in the motor 1 enable jumper (ENA) as we will use only the A output terminals.
Connect pin 4 of the motor driver to positive voltage output pin (OUT +) of DC-DC upscaler and pin 5 to the negative upcaler output pin (OUT -). 

If you are not using the switching general purpose transistor, then connect pin 6 to PIN 2 (5V) of your RPi to feed in logical voltage. Next wire pins 16 (GPIO23) and 18 (GPIO24) of your RPi to motor driver pins 8 (IN1) and 9 (IN2).

Connect the motor driver pins 1 and 2 (output terminals for motor A) to clock terminals.

Alternatively, if you want to use the switching general purpose transistor, then connect the RPi pin 2 (5V) to the anode of the transistor, the RPi pin 22 (GPIO25) to the transistor's base and the cathode of the transistor to pin 6 (5V) of the L298 motor driver.

## Install the App
We will install the application by downloading required python packages using pip and cloning the python source files from git repository.

#### Install Pip3
The app uses python3, so make sure you use the correct python version also for pip. To be on the safe side use pip and python commands with 3 at the end.
```
sudo apt-get install python3-pip
```

#### Install Required Modules (Python3)
- RPi-GPIO
```
sudo apt-get install python3-rpi.gpio
```

- APscheduler (3.5.1)
```
sudo pip3 install apscheduler
```

- Flask (1.0.2)
```
sudo pip3 install flask
```

#### Clone the repository
First install GIT if you have not done so before
```
sudo apt-get install git-core
```
and then clone the repository with command
```
cd ~
git clone https://github.com/dorsic/pragoPi
```
This will create a new directory pragoPi under your home directory and download the source files.

### Test the App
Now we are ready to test the app. To start the application run the `app.py` script.
```
cd ~/pragoPi
sudo python3 app.py
```
Flask web server will start to listen on port 80 for requests. If you issue the impulse request opening your web browser with URL `http://pragoPi:80/impulse` or  using `curl` command
```
curl -XGET http://pragoPi:80/impulse
````
your watch should progress one minute.

To set the time of the watch, you need to tell the app what time is the watch displaying. What is the position of the watch hands right now. To do this you can either edit the `clockStatus.conf` file and set the *displayedTime* property to the time shown by the clock, e.g. *11:19* or you can use the web API `setTime` request where you specify the time displayed by the clock as the URL parameter. You can use either 12- or 24-hour format, just leave out the separator (*:*) and leading zeros. Again the request can be sent via the web browser, just go to URL `http://pragoPi:80/setTime/2132` for example or using the `curl` command, e.g.
```
curl -XGET http://pragoPi:80/setTime/2132
```

Once again, that the parameter after the slash (*2132*) is the time displayed by your clock not current time. Since the RPi knows current time via NTP it advances the clock until the time displayed is in line with current time. 

Note, that all sample commands assume your RPi host name is pragoPi. If not, please alter the commands respectively.

##### Install System Service
In case of power outage and recovery we want the clock to automatically boot and set correct time. For this reason, current displayed time is stored to an permanent memory - file on the SD card and we create a Linux service, that will start the program upon boot.

To create the Linux service copy the `pragopi.service` service definition file to system services and set appropriate file access permissions.
```
sudo cp pragopi.service /lib/systemd/system 
sudo chmod 644 /lib/systemd/system/pragopi.service
chmod +x /home/pi/pragoPi/app.py
```

Now the services daemon can be reloaded to read the new service and we will enable and start the service. For this use these commands:

```
sudo systemctl daemon-reload
sudo systemctl enable pragopi.service
sudo systemctl start pragopi.service
```


### Web API
- Move clock one minute forward
`curl -XGET http://pragoPi:80/impulse`
- Set time
`curl -XGET http://pragoPi:80/setTime/<displayedTime>`
where *displayedTime* is the current time showed by the clock in HHMM format. Both 12- and 24- hour time formats are supported.

## Further extensions

The clockc is a 24/7 device so it is worth to pay attention to power consumption. You can apply some of the power saving techniques as:
- throttle down the cpu
- turn off unnecessary components and chips (e.g. usb and bluetooth)

Furthermore you can experiment with your own time source. You can extend the system with an RTC module or hook in a local PPS source derived from power line frequency to better overcome internet outages. Note that powerline frequency is quite a good time source and is managed to be alligned with UTC. You can check current status e.g. on [swiss grid](https://www.swissgrid.ch/en/home/operation/grid-data/current-data.html). 
But nowadays is wifi so common as the electricity and playing with 220V power lines requires knowledge and paying extra attention.



*If you think the project documentation needs enhancement in some chapters I would be happy to do so.*
