Joystick Gremlin
================

Introduction
------------

Joystick Gremlin is a program that allows the configuration of joystick like
devices, similar to what CH Control Manager and Thrustmaster's T.A.R.G.E.T. do
for their respectively supported joysticks. However, Joystick Gremlin works
with any device be it from different manufacturers or custom devices that
appear as a joystick to Windows. Joystick Gremlin uses the virtual joysticks
provided by vJoy to map physical to virtual inputs and apply various other
transformations such as response curves to analogue axes. In addition to
managing joysticks, Joystick Gremlin also provides keyboard macros, a flexible
mode system, scripting using Python, and many other features.

The main features are:
- Works with arbitrary joystick like devices
- User interface for common configuration tasks
- Merging of multiple physical devices into a single virtual device
- Axis response curve and dead zone configuration
- Arbitrary number of modes with inheritance and customizable mode switching
- Keyboard macros for joystick buttons and keyboard keys
- Python scripting

Joystick Gremlin provides a graphical user interface which allows commonly
performed tasks, such as input remapping, axis response curve setups, and macro
recording to be performed easily. Functionality that is not accessible via the
UI can be implemented through custom modules. 


Used Software & Other Sources
-----------------------------
Joystick Gremlin uses the following software and resources:

- [pyinstaller](http://www.pyinstaller.org/)
- [PyQT5](http://www.riverbankcomputing.co.uk/software/pyqt/intro)
- [PyWin32](http://sourceforge.net/projects/pywin32)
- [vJoy](http://vjoystick.sourceforge.net)
- [Python 3.4](https://www.python.org)
- [Modern UI Icons](http://modernuiicons.com/)

Currently the 32bit version of Python is needed and the following packages should be installed via PiP to get the source running:
 
 - PyQT5
 - pypiwin32
 
Update:

Looks like he relies on a bunch of stuff that isn't properly configured in the environment. These are the steps needed to create the environment from scratch:

```
conda create -n joystick_gremlin32 python=3.6
conda activate joystick_gremlin32
conda config --env --set subdir win-32 # this sets the env platform to win 32-bit
conda install python=3.6  # this re-installs 32-bit python 3.6
pip install pyqt5
pip install pypiwin32
conda install reportlab   # needed for the cheatsheet
```
Generating the MSI Installer
----------------------------

The job of turning the Python code in a windows executable and
packaging everything up into an installable MSI file is performed
by [pyinstaller](http://www.pyinstaller.org/) and
[wix](http://wixtoolset.org/). The steps needed to build the code
and assemble it into the installer is automated using a batch
script and can be run as:
  ```
  deploy.bat
  ```
To simply generate the executable code without the MSI installer the
following command can be used:
  ```
  pyinstaller -y --clean joystick_gremlin.spec
  ```

Missing a bunch of modules this way. Unclear if they need to be installed manually - try again tomorrow.