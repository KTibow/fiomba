# fiomba
Documenting Fiomba, a project to turn old Roombas into smart ones.  
Warning: This project is for makers, not people who are just getting started with Raspberry Pi.  
To make Fiomba, first get a [Roomba to USB cable](https://store.irobot.com/default/parts-and-accessories/create-accessories/communication-cable-for-create-2/4466502.html) from iRobot.  
Then, you're going to need a [5v converter](https://www.adafruit.com/product/1385) from Adafruit.  
You'll also need a [USB adapter](https://www.adafruit.com/product/1099) because you're going to be using a [Pi Zero](https://www.adafruit.com/product/3708). And of course you'll need a [SD card](https://www.adafruit.com/product/2693) too.  
Don't forget your Roomba! Fiomba works with Roombas in the 500 and 600 series. In my case, I had to get an [OSMOPod](https://homesupport.irobot.com/app/answers/detail/a_id/124/~/how-do-i-update-the-software-of-my-non-wi-fi-connected-roomba%C2%AE-with-an-osmo%3F) from iRobot.  
And the backbone for Fiomba is [Home Assistant](https://www.home-assistant.io/), so make sure that's set up with MQTT.
Okay! Let's get started!  
  
First, you'll need to set up the SD card. Use Raspbian Lite. Some great guides are these:

- https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up/2
- https://www.raspberrypi.org/documentation/configuration/wireless/headless.md

Enable SSH. Yay! Your SD card is ready!  
Now, find a good power source. Make sure it has at least 2 amps, or 2000 mA. It shouldn't be too massive; don't use one with greater than 3 amps or 3000 mA. Put the SD card into your Pi Zero's microSD slot. Ready? Use a microUSB cable to plug a cable into the port that says "PWR". The green LED should start flickering! Now, wait 1 minute.  
Install ssh on your computer. If you're not on the latest version of Windows, you may need to download [PUTTY](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html). Make sure you download the full version.  
Okay! Now, connect to the same network as your Pi Zero. Open the terminal, and type in:  
`ssh pi@raspberrypi`  
If it works, it should say something like  
```
The authenticity of host 'raspberrypi (192.168.something.something)' can't be established.
ECDSA key fingerprint is SHA256:somethingsomethingsomething.
Are you sure you want to continue connecting (yes/no)?
```
If it says something other than 192.168.something.something, then there's a problem. Type in "no" and press enter. Otherwise, it worked, so type in "yes" and press enter!  
Next, you should type in `sudo raspi-config`. Use the arrow keys and enter to navigate. Get everything set up. Yay!  
Now you need to download fiomba. Type this in and press enter:  
`wget https://raw.githubusercontent.com/KTibow/fiomba/master/fiomba.py`  
That should download fiomba. You need to edit it, though. Type this in and press enter:  
`nano fiomba.py`  
Navigate with the arrow keys, and change the Home Assistant creds. Press Ctrl+X and enter to save.  
Okay! Now, type in `sudo shutdown now`. That'll shut down the pi. After 30 seconds or 5 seconds after the pi's led stops blinking, unplug it. Yay! On to hardware!  
