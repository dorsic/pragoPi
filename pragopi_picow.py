import machine  
import time
import network
try:
  import usocket as socket
except:
  import socket

import ntptime

ssid = 'xxx'
password = 'xxx'

class PragoPi():
    led = machine.Pin('LED', machine.Pin.OUT)
    pwr_en = machine.Pin(15, machine.Pin.OUT)
    impl_pos_pin = machine.Pin(16, machine.Pin.OUT)
    impl_neg_pin = machine.Pin(17, machine.Pin.OUT)
    
    wlan = None
    ip = None
    tim = None	# minute timer
    dtim = None # day timer for ntp.settime
    wdt = None	# watchdog timer
    displayed_time = -1		# 0..719	720 = 12h * 60min
    min_len_s = 60 # ToDo: in production must be 60
    
    _last_imp = 0
    LONG_PULSE = 1.5
    SHORT_PULSE = 0.1 # 0

    def __init__(self):
        #self.wdt = machine.WDT(timeout=8000)  # 130 seconds
        #self.wtim = machine.Timer(period=6000, mode=machine.Timer.PERIODIC, callback=lambda t:self.wdt.feed())
        self.pwr_en.low()
        self.impl_pos_pin.low()
        self.impl_neg_pin.low()
        self.last_impulse = 0
        self.wlan = network.WLAN(network.STA_IF)
        self._jobid = 0
            
    def connect(self, ssid=ssid, password=password):
        print(f'connecting to {ssid}')
        self.wlan.active(True)
        self.wlan.connect(ssid, password)
        while self.wlan.isconnected() == False:
            n = 8
            for i in range(8):
                if self.wlan.isconnected():
                    break
                self.led.on()
                time.sleep(0.1)
                print('Waiting for connection...')
                self.led.off()
                time.sleep(0.9)
            if self.wlan.isconnected() == False:
                self.wlan.active(False)
                self.wlan.active(True)
                self.wlan.connect(ssid, password)
                print('Reconnecting self.wlan...')
        print(self.wlan.ifconfig())
        self.ip = self.wlan.ifconfig()[0]
        print(f'Connected on {self.ip}')
        print(f'local time: {time.localtime()}')
        self.displayed_time = self._to_display_time()
        return self.ip

    def _to_display_time(self, ts=None):
        t = ts if ts else time.localtime()
        #return (t[3]%12)*60 + t[4]
        dt = (t[3]%12)*3600 + t[4]*60 + t[5]
        dt = round(dt/self.min_len_s) * self.min_len_s
        return dt
    
    def _str_to_display_time(self, ts):
        s = ts.replace(':', '').strip()
        si = int(s)
        if len(s) > 4:
            return ((si//10000)%12) * 3600 + ((si//100)%100) * 60 + (si%100)
        return ((si//100)%12) * 3600 + (si%100) * 60

    def _display_time_to_str(self, dt):
        return f'{dt//3600:02}:{(dt//60)%60:02}:{dt%60:02}'
        
    def _time_to_str(self, ts=None):
        t = ts if ts else time.localtime()
        return f'{t[3]:02}:{t[4]:02}:{t[5]:02}'
            
    def _inc_display_time(self, dt):
        return (dt+self.min_len_s) % 43200
    
    def start_time(self):
        self.once_a_day()        
        self.dtim = machine.Timer(period=86400000, mode=machine.Timer.PERIODIC, callback=lambda t:self.once_a_day())
        
    def _of_minute_top(self):
        lt = time.localtime()
        wt = (lt[5]+1) % self.min_len_s
        return wt

    def start_minuter_job(self):
        if self.tim:
            self.tim.deinit()
            time.sleep(0.1)
                    
        wt = self._of_minute_top()
        if wt > 3:
            wt = self.min_len_s - wt + 1
            print(f'waiting for top of the second {wt} s')
            time.sleep(wt-1)
        self.tim = machine.Timer(period=self.min_len_s*1000, mode=machine.Timer.PERIODIC, callback=lambda t:self.once_a_minute(self._jobid))
        self._jobid += 1
        
    def stop_minuter_job(self):
        print(f'stopping job {self._jobid} ', end='')
        if self.tim:
            self.tim.deinit()
            time.sleep(0.1)
            self.tim = None
            self._jobid -= 1
            print('done')
        else:
            print(' no job')

    def start_server(self):
        # expects 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 80))
        s.listen(3)
        
        while True:
            try:
                conn, addr = s.accept()
                conn.settimeout(3.0)
                print(f'Received HTTP GET connection request from {addr}')
                request = conn.recv(1024)
                conn.settimeout(None)
                request = str(request)
                print(f'GET Request Content = {request}')
                
                tstart = request.find('/')+1
                tend=request.find('HTTP')
                new_disp_time = request[tstart:tend].strip()
                if new_disp_time:
                    try:
                        new_disp_time = self._str_to_display_time(new_disp_time)                        
                        print(f'New display time value: {new_disp_time}')
                        self.set_displayed_time(new_disp_time, start_job=True)
                        response='OK\n'
                    except:
                        response=f"Invalid value '{new_disp_time}', must be in format hh[:]mm[:][ss].\n"
                else:
                    response=f'{self.displayed_time} - {self._display_time_to_str(self.displayed_time)}\n'
                
                conn.send('HTTP/1.1 200 OK\n')
                conn.send('Content-Type: text/plain\n')
                conn.send('Connection: close\n\n')
                conn.sendall(response)
                conn.close()
            except OSError as e:
                conn.close()
                print('Connection closed')
    
    def set_displayed_time(self, displaying_time=None, start_job=True):
        # move clock hands to display_time
    
        # disable schedule
        self.stop_minuter_job()
        cdt = displaying_time if displaying_time else self.displayed_time
        if not cdt:
            print("Unknown display time. Cannot set time.")
            return

        tnow = self._to_display_time()
        while (cdt != tnow):
            self.progress_display_time(self.SHORT_PULSE)
            cdt = self._inc_display_time(cdt)
            tnow = self._to_display_time()

        self.displayed_time = cdt
        if start_job:
            print(f'Done setting displayed time. Resuming scheduler.')        
            self.start_minuter_job()        
                    
        
    def write_status(self):        
        # save self.displayed_time and self.last_impulse to persistent memory (file)
        return
    
    def progress_display_time(self, impulse_len=None):
        # may restart the minuter_job if out of top_minute sync
        try:
            self.led.low()
            pin = self.impl_neg_pin if self.last_impulse > 0 else self.impl_pos_pin        
            pin.high()
            il = impulse_len if impulse_len is not None else self.LONG_PULSE
            time.sleep(il)
            pin.low()        
            self.displayed_time = self._inc_display_time(self.displayed_time)
            lt = time.localtime()
            li = time.ticks_ms()
            print(f'{self.last_impulse:+} Impulse done. {self._time_to_str(lt)} ({self._to_display_time(lt):4}), {self.displayed_time:5}, il = {il:1.1f}, dt = {li - self._last_imp:6}')
            self._last_imp = li
            self.last_impulse = -1 if self.last_impulse > 0 else 1
            self.led.high()  
        except KeyboardInterrupt:
            self.stop_minuter_job()
            machine.reset()
    
    def get_ntptime(self):
        # may reconnect the WiFi on Error
        # may lifelock if no WiFi can be connected
        nt, n = None, 0
        while not nt:
            try:
                nt = ntptime.time()
                if time.localtime(nt)[0] > 2030:
                    nt = None
            except OSError as e:
                n += 1
                if n > 5:
                    self.wlan.active(False)
                    time.sleep(0.5)
                    self.connect()
                    n = 0
                else:
                    time.sleep(1)
        return nt

    def set_time(self):
        # sets local time from ntpd
        nt = self.get_ntptime()
        dh = round((time.time()-nt)/3600)
        if (dh < -13) or (dh > 13):
            return
        print(f'local time: {time.localtime()} {dh:+}')

        nt = nt + 3600*dh
        nt = list(time.localtime(nt))

        nt = nt[:3] + [nt[6]] + nt[3:6] + [nt[7]]	# day of week in rtc is on index 3
        machine.RTC().datetime(nt)        
        print(f'new time: {time.localtime()} {dh:+}')

    def once_a_minute(self, jobid):
        print(f"jobid: {jobid}")
        self.progress_display_time()
        wt = self._of_minute_top()
        if wt > 6:
            print(wt)
            self.start_minuter_job()
        self.write_status()
        
    def once_a_day(self):
        #self.stop_minuter_job()
        if self.wlan.isconnected() == False:
            # reconnect if needed
            self.wlan.active(False)
            time.sleep(0.5)
            self.connect()
            # the time is now updated also
        # update the time
        self.stop_minuter_job()
        self.set_time()
        self.set_displayed_time(start_job=True)
        self.write_status()
    
try:
    pp = PragoPi()
    pp.start_time()
    pp.start_server()
    
except KeyboardInterrupt:
    if pp.tim:
        pp.tim.deinit()
        del(pp.tim)
    machine.reset()
