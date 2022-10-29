#  main_rc_pio.py

import RemoteControlPIO as RemoteControl
utime = RemoteControl.utime

class ThisStateMachine1(RemoteControl.StateMachine):
    #  reads remote control channel 1 (right joystick sideways)
    def __init__(self):
        name = 'RC Channel 1'
        code = 'MEASURE'
        pin_no = 7
        super().__init__(name, code, pin_no)

class ThisStateMachine2(RemoteControl.StateMachine):
    #  reads remote control channel 2 (right joystick up down)
    def __init__(self):
        name = 'RC Channel 2'
        code = 'MEASURE'
        pin_no = 6
        super().__init__(name, code, pin_no)

class ThisRightSideways(RemoteControl.Joystick):
    def __init__(self):
        state_machine = ThisStateMachine1()
        interpolator = RemoteControl.Interpolator([49, 74, 76, 101],[-100.0, 0.0, 0.0, 100.0])
        name = 'Right Sideways'
        super().__init__(name, state_machine, interpolator)

class ThisRightUpDown(RemoteControl.Joystick):
    def __init__(self):
        state_machine = ThisStateMachine2()
        interpolator = RemoteControl.Interpolator([49, 74, 76, 101],[-100.0, 0.0, 0.0, 100.0])
        name = 'Right Up Down'
        super().__init__(name, state_machine, interpolator)

my_right_sideways = ThisRightSideways()
my_right_up_down = ThisRightUpDown()

for i in range(10):
    utime.sleep_ms(500)
    print ("updown {:04},  sideways {:04}".format(my_right_up_down.get(), my_right_sideways.get()))

my_right_sideways.close()
my_right_up_down.close()