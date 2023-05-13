import RPi.GPIO as GPIO
import time
import os
from threading import Timer, Lock
from omxplayer.player import OMXPlayer


class VidLooper:

    GPIO_BOUNCE_TIME = 2000
    switch_lock = Lock()
    delay_threshold = 0.4
    over_time_threshold = 3


    def __init__(self):
        """
        - If there are less than 8 videos, remove the unnessary GPIO pins from the list
        - Assemble the list of videos to play
        - Merge active videos and store lengths
        """
        self.read_video_data() 

        self.player = OMXPlayer('/home/pi/videos/combined.mp4')

        self.snip_timer = Timer(self.active_videos[0] - self.over_time_threshold, self.gpio_switch_vid, ['bb'])
        self.snip_timer.start()

        self.start()   


    def read_video_data(self):
        """
        - Check if videos and length file exist 
        - Read in durations of videos from length.txt
        """
        self.active_videos = []

        try:
            with open('/home/pi/videos/length.txt', 'r') as length_file:
                for line in length_file:
                    duration = float(line.rstrip())
                    self.active_videos.append(duration)
        except:
            raise Exception('Add length.txt file to SD card at /home/pi/videos/ in RootFS Partition')

        if not os.path.exists('/home/pi/videos/combined.mp4'):
            raise Exception('Add combined.mp4 file to SD card at /home/pi/videos/ in RootFS Partition')

        self.get_switch_times()
        self.prune_pins()


    def get_switch_times(self):
        """
        - Map durations of video clips to change times 
        """
        self.switch_times = []
        
        start = 0
        for vid_time in self.active_videos:
            self.switch_times.append(start + self.delay_threshold)
            start += vid_time

    
    def prune_pins(self):
        """
        - Removing GPIO pins not being used  
        """
        self.gpio_pins = [
            17, # TR1
            27, # TR2 
            22, # TR3 
            10, # TR4 
            6,  # TR5
            13, # TR6
            19, # TR7
            26, # TR8
        ]

        for i in range(len(self.gpio_pins) - len(self.active_videos)):
            self.gpio_pins.pop()


    def gpio_switch_vid(self, pin):
        """
        - Set as callback for GPIO 
        - Switch video by setting position to stored value 
        """
        with self.switch_lock:
            if pin == 'bb':
                self.snip_timer = Timer(self.active_videos[0] - self.over_time_threshold, self.gpio_switch_vid, ['bb'])
                self.snip_timer.start()                
                self.player.set_position(self.switch_times[0])

            else:
                self.snip_timer.cancel()
                self.snip_timer = Timer(self.active_videos[self.gpio_pins.index(pin)] - self.over_time_threshold, self.gpio_switch_vid, ['bb'])
                self.snip_timer.start()
                self.player.set_position(self.switch_times[self.gpio_pins.index(pin)])


    def start(self):
        """
        - Clearing screen and removing blinking cursor 
        - Setting GPIO to broadcom reference
        - Setting active pins 
        - 
        """
        os.system('clear')
        os.system('tput civis')
        
        GPIO.setmode(GPIO.BCM)

        for p in self.gpio_pins:
            GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
        
        for pin in self.gpio_pins:
            GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.gpio_switch_vid, bouncetime=self.GPIO_BOUNCE_TIME)


if __name__ == '__main__':
    loop = VidLooper()

    # while True:
    #     pass