# Import libraries.
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from time import sleep, time, localtime
import serial
from os import system

# Some stuff for recieving commands.
lastCommand = ""
def command(client, userdata, message):
    global lastCommand
    lastCommand = message.payload.decode()

# Connect MQTT
print("Connecting...")
client = mqtt.Client("Roomba")
# I'm using Home Assistant MQTT with the Mosquitto plugin.
client.username_pw_set("YourHomeAssistantUsername", password="your_password")
# Home Assistant's MQTT local hostname is homeassistant.
# I think it would work without the .home though.
client.connect("homeassistant.home")
# Subscribe to commands.
client.subscribe("vacuum/command")
client.message_callback_add("vacuum/command", command)
client.publish("vacuum/status", "online")
# Connect to Roomba.
roomba = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.1)
print("Connected")

# Set the state over MQTT.
# https://www.home-assistant.io/integrations/vacuum.mqtt/
# State config
def sendState(level, state):
    client.publish("vacuum/state", '{"battery_level": '+str(level)+', "state": "'+state+'"}')

# Make byte from number.
# This is kind of hacky, but Python didn't work that well with this.
def byte(number):
    if number < 16:
        return bytes.fromhex('0'+hex(number)[2:3])
    else:
        return bytes.fromhex(hex(number)[2:4])

# Start it up!
# This tells MQTT to start sending and recieving messages.
client.loop_start()
# Various variables.
lastState = ""
lastBattery = -1
state = ""
shuttingdown = False
i = 0
age = time()
# Loop.
while True:
    # Get sensors. I used to use a stream, but it didn't work that well.
    roomba.write(b'\x95')
    # Clear out previous data
    roomba.read_all()
    # Explanation:
    # The first sensor is Charging Sources Available, packet ID 34
    # It tells me if the Roomba is docked
    # The second sensor is Main Brush Motor Current, packet ID 56
    # It tells me if the Roomba is cleaning
    # The third sensor is Right Motor Current, packet ID 55
    # It tells me if the Roomba is cleaning
    # The fourth sensor is Battery Charge, packet ID 25
    # It tells me how charged up the Roomba is
    # The fifth sensor is Battery Capacity, packet ID 26
    # It tells me how charged up the Roomba is
    roomba.write(b'\x05\x22\x38\x37\x19\x1A')
    sleep(0.03)
    # Parse the return.
    charging = int.from_bytes(roomba.read(1), byteorder='big')
    cleaning1 = int.from_bytes(roomba.read(2), byteorder='big')
    cleaning2 = int.from_bytes(roomba.read(2), byteorder='big')
    level = int.from_bytes(roomba.read(2), byteorder='big')
    cap = int.from_bytes(roomba.read(2), byteorder='big')
    # Assume the Roomba is on.
    on = True
    # Print response for troubleshooting.
    print("Response: Charging: "+str(charging)+", Cleaning: "+str(cleaning1)+", "+str(cleaning2)+", Capacity: "+str(level)+"/"+str(cap))
    # Is the roomba on?
    # If it's asleep, it won't send anything when I ask it for sensors.
    # The other sensors can all be 0, but Battery Capacity *and* Battery Charge are only zero when the Roomba is asleep.
    if level == 0 and cap == 0:
        # We don't know what it's doing. If it's cleaning, it has to be awake.
        # If it changes states, it has to be awake.
        # So we can assume that if it's not awake, it was in the same state as last time.
        if state != "docked":
            state = "idle"
        # It's not on, because it didn't send anything. Set on to false.
        on = False
        # Wake it up every 10 minutes.
        if i % 200 == 0:
            print("Wakey wakey!")
            # The Roomba's awake now. Set on to true.
            on = True
            # Wake the Roomba with the serial port.
            roomba.close()
            roomba.open()
            # Put it into passive mode.
            roomba.write(b'\x80')
            sleep(0.1)
            # It didn't send anything earlier, so ask it for stuff now that it's awake.
            # Refer to line 56 for sensor explanation.
            roomba.write(b'\x95')
            roomba.read_all()
            roomba.write(b'\x05\x22\x38\x37\x19\x1A')
            sleep(0.02)
            charging = int.from_bytes(roomba.read(1), byteorder='big')
            cleaning1 = int.from_bytes(roomba.read(2), byteorder='big')
            cleaning2 = int.from_bytes(roomba.read(2), byteorder='big')
            level = int.from_bytes(roomba.read(2), byteorder='big')
            cap = int.from_bytes(roomba.read(2), byteorder='big')
            print("Response: Charging: "+str(charging)+", Cleaning: "+str(cleaning1)+", "+str(cleaning2)+", Capacity: "+str(level)+"/"+str(cap))
            # Set clock.
            roomba.write(b'\x85')
            print("Setting time...")
            theTime = localtime(time())
            roomba.write(b'\xA8'+byte((theTime[6]+1)%7)+byte(theTime[3])+byte(theTime[4]))
            print("Time set.")
    elif i % 200 == 0 and (state == "docked" or state == "idle"):
        # If it's awake and not cleaning, every 10 minutes, set the time.
        print("Setting time...")
        theTime = localtime(time())
        roomba.write(b'\xA8'+byte((theTime[6]+1)%7)+byte(theTime[3])+byte(theTime[4]))
        print("Time set.")
    # Find state if it was on.
    if on:
        # If the response from charging (packet ID 34) wasn't no charging source, say that it's docked.
        if charging != 0:
            state = "docked"
        else:
            # Is the main brush or the right wheel turning? It's cleaning.
            if cleaning1 != 0 or cleaning2 != 0:
                state = "cleaning"
            else:
                # It's doing nothing. It's idle. (I don't know how to tell if there's an error)
                state = "idle"
    # Send state
    try:
        # Get percentage
        battery = round(level/cap*100)
    except ZeroDivisionError:
        # If it's not on and it sent 0 for capacity, use the last reading.
        battery = lastBattery
    # If the battery's low, and it's not docked, and it's currently not shutting down, shutdown in 1 minute.
    if battery < 30 and state != "docked" and not shuttingdown:
        system("sudo shutdown")
        shuttingdown = True
    # If the battery's good and it's currently shutting down, cancel the shutdown.
    elif battery >= 30 and shuttingdown:
        system("sudo shutdown -c")
        shuttingdown = False
    # If something has changed since the last time I got the sensor values, or I haven't send a new value in 3 minutes,
    # send the current state.
    if battery != lastBattery or state != lastState or time() - age > 180:
        sendState(battery, state)
        age = time()
        print("Status sent: "+str(battery)+"% ("+str(level)+"/"+str(cap)+"), "+state)
    lastState = state
    lastBattery = battery
    # i is a tick mark for every loop.
    i += 1
    # Now we sleep, so we don't hammer the Roomba. If there's a new instruction, execute it.
    try:
        for j in range(30):
            if lastCommand != "":
                # Wake up the Roomba and set it to passive.
                print("Instruction: "+lastCommand)
                roomba.close()
                roomba.open()
                roomba.write(b'\x80')
                sleep(0.1)
                if lastCommand == "start":
                    # Go into safe mode and start the Roomba on a normal cycle.
                    roomba.write(b'\x83')
                    sleep(0.05)
                    roomba.write(b'\x87')
                    roomba.read_all()
                elif lastCommand == "pause":
                    # Pause the Roomba by going into and out of safe mode.
                    roomba.write(b'\x83')
                    sleep(0.05)
                    roomba.write(b'\x80')
                    sleep(0.05)
                    roomba.read_all()
                elif lastCommand == "locate":
                    # Go into safe mode, play a tone, and go out.
                    roomba.write(b'\x83')
                    sleep(0.05)
                    roomba.write(b'\x8C\x00\x08\x32\x10\x37\x10\x3C\x10\x37\x10\x32\x10\x37\x10\x3C\x10\x37\x10')
                    sleep(0.005)
                    roomba.write(b'\x8D\x00')
                    sleep(2)
                    roomba.write(b'\x80')
                    roomba.read_all()
                elif lastCommand == "return_to_base":
                    # Go into safe mode and tell the Roomba to go home.
                    roomba.write(b'\x83')
                    sleep(0.05)
                    roomba.write(b'\x8F')
                    roomba.read_all()
                lastCommand = ""
            # Sleep 0.1 seconds. We repeat this cycle 30 times.
            sleep(0.1)
    # If somebody interrupts, break.
    except KeyboardInterrupt:
        break
