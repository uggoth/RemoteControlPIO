#  RemoteControl_v06.py

import utime
import rp2
import machine

class GPIO():

    valid_pin_nos = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,26,27,28,29]
    valid_type_codes = {'INFRA_RED':'INPUT',
                        'BUTTON':'INPUT',
                        'US_TRIGGER':'OUTPUT',
                        'US_ECHO':'INPUT',
                        'SWITCH':'INPUT',
                        'VOLTS':'INPUT',
                        'LED':'OUTPUT',
                        'CONTROL':'INPUT',
                        'MOTOR':'OUTPUT'}
    allocated = {}
    allocated_by_type = {}
    allocated_str = ''
    for type_code in valid_type_codes:
        allocated_by_type[type_code] = {}
    
    def __init__(self, pin_no, type_code, name):
        self.valid = False
        if pin_no not in GPIO.valid_pin_nos:
            print (pin_no,'not in',GPIO.valid_pin_nos)
            return
        self.pin_no = pin_no
        if type_code not in GPIO.valid_type_codes:
            print (type_code,'not in',GPIO.valid_type_codes)
            return
        self.type_code = type_code
        if self.pin_no in GPIO.allocated:
            print (self.pin_no,'already allocated')
            return
        self.name = name
        self.valid = True
        self.previous = 'UNKNOWN'
        GPIO.allocated[self.pin_no] = self
        GPIO.allocated_by_type[self.type_code][self.pin_no] = self
        GPIO.allocated_str += str(self.pin_no) + ':' + self.name + ':' + str(self) + '\n\r'
        
    def str_allocated():
        out_string = ''
        for device in sorted(GPIO.allocated):
            obj = GPIO.allocated[device]
            out_string += ('{:02}'.format(device) + ' : ' +
                            '{:18}'.format(obj.name) + ' : ' +
                            str(obj) + "\n")
        return out_string
    
    def deallocate(pin_no):  #  ***** IMPLEMENT LATER *********
        pass
    
class Sensor(GPIO):
    sensor_list = []
    def __init__(self, pin_no, type_code, name):
        super().__init__(pin_no, type_code, name)
        if not self.valid:
            return
        self.state = 'UNKNOWN'
        Sensor.sensor_list.append(self)

class ControlPin(Sensor):
    def __init__(self, pin_no, name):
        self.type = 'CONTROL'
        super().__init__(pin_no, self.type, name)
        self.pin_no = pin_no
        self.pin = machine.Pin(self.pin_no, machine.Pin.IN, machine.Pin.PULL_DOWN)
    

@rp2.asm_pio()
def measure():
    wrap_target()
    wait(0,pin,0)  #  don't start in the middle of a pulse
    wait(1,pin,0)
    mov(x,invert(null))
    label('loop')
    jmp(x_dec,'pin_on') #  Note: x will never be zero. We just want the decrement
    nop()
    label('pin_on')
    jmp(pin, 'loop')
    mov(isr,invert(x))
    push(noblock)
    wrap()

class StateMachine():
    
    valid_state_machine_nos = [7,6,5,4,3,2,1,0]
    valid_codes = ['MEASURE']
    allocated = {}
    
    def __init__(self, name, code, pin_no, hertz=100000):
        self.valid = False
        if code not in StateMachine.valid_codes:
            return None
        self.name = name
        self.pin_no = pin_no
        self.gpio = ControlPin(self.pin_no, self.name + '_control')
        self.pin = self.gpio.pin
        self.value = None
        # print (StateMachine.allocated)
        for state_machine_no in StateMachine.valid_state_machine_nos:
            str_no = str(state_machine_no)
            if ((str_no not in StateMachine.allocated) or (StateMachine.allocated[str_no] == 'None')):
                if code == 'MEASURE':
                    self.instance = rp2.StateMachine(state_machine_no, measure, freq=hertz, in_base=self.pin, jmp_pin=self.pin)
                StateMachine.allocated[str_no] = self.name
                self.valid = True
                self.state_machine_no = state_machine_no
                self.instance.active(1)
                break
    def get_next_blocking(self):
        self.value =  self.instance.get()
        return self.value
    def get_latest(self):
        self.value = None
        while self.instance.rx_fifo():
            self.value = self.instance.get()
        return self.value
    def close(self):
        if self.valid:
            self.instance.active(0)
            str_no = str(self.state_machine_no)
            StateMachine.allocated[str_no] = 'None'
            GPIO.deallocate(self.pin_no)


class Joystick():
    def __init__(self, name, state_machine, interpolator):
        self.name = name
        self.state_machine = state_machine
        if not self.state_machine.valid:
            print ('**** bad sm', self.state_machine.name)
        self.interpolator = interpolator
        if interpolator is not None:
            self.previous = self.interpolator.interpolate(75)
        else:
            self.previous = 75  #  mid point
    def close(self):
        self.state_machine.close()
    def get(self):
        value = self.state_machine.get_latest()
        if self.interpolator is not None:
            if value is not None:
                self.position = self.interpolator.interpolate(value)
                if self.position != self.previous:
                    self.previous = self.position
            return self.previous
        else:
            return value

class Interpolator():
    def __init__(self, keys, values):  #  arrays of matching pairs
                                        # keys ascending integers
                                        # values any floats
        self.keys = keys
        self.values = values
    def interpolate(self, in_key):  #  input is integer
        if in_key is None:
            return None
        below_ok = False
        above_ok = False
        for i in range(len(self.keys)):
            if in_key == self.keys[i]:
                return self.values[i]
            if in_key > self.keys[i]:
                below_key = self.keys[i]
                below_value = self.values[i]
                below_ok = True
            if in_key < self.keys[i]:
                above_key = self.keys[i]
                above_value = self.values[i]
                above_ok = True
                break
        if above_ok and below_ok:
            out_value = below_value + (((in_key - below_key) / (above_key - below_key)) * (above_value - below_value))
            return out_value
        else:
            return None

if __name__ == "__main__":
    print ("RemoteControlPIO.py\n")
