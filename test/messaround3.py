import time
class Clock(object):

    def __init__(self,seconds=0, minutes=0, hours=0 ):
        if seconds > 59:
            minutes = seconds // 60
            seconds %= 60
        if minutes > 59:
            hours = minutes // 60
            minutes %= 60
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    def tick(self):
        """ Time will go down by one second"""
        while True:
            if self.seconds <10:
                z = '0'+str(self.seconds)
            else:
                z = str(self.seconds)
            if self.minutes < 10:
                y = '0'+str(self.minutes)
            else:
                y = str(self.minutes)
            if self.hours < 10:
                x = '0'+str(self.hours)
            else:
                x = str(self.hours)
            print("\r" + x + ":" + y + ":" + z,)
            time.sleep(1)
            self.seconds -= 1
            if self.seconds == -1:
                if self.minutes != 0:
                    self.seconds = 59
                    self.minutes -= 1
                else:
                    if self.hours != 0:
                        self.minutes = 59
                        self.hours -= 1
            if z == '00' and y == '00' and x == '00':
                break

        print("\rBLASTOFF!")
        time.sleep(1)

input = input('How many seconds?')
x = Clock(int(input))
x.tick()