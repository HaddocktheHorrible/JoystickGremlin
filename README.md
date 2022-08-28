# Joystick Gremlin

## Introduction

---

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

## Used Software & Other Sources

---

Joystick Gremlin uses the following software and resources:

- [pyinstaller](http://www.pyinstaller.org/)
- [PyQT5](http://www.riverbankcomputing.co.uk/software/pyqt/intro)
- [PyWin32](http://sourceforge.net/projects/pywin32)
- [vJoy](http://vjoystick.sourceforge.net)
- [Python 3.4](https://www.python.org)
- [Modern UI Icons](http://modernuiicons.com/)

Currently the 32bit version of Python is needed. To create and activate a conda environment with the required modules, simply call:

```bash
conda env create -f conda_env.yaml
conda activate joystick_gremlin32
```

## Generating the MSI Installer

---

The job of turning the Python code in a windows executable and
packaging everything up into an installable MSI file is performed
by [pyinstaller](http://www.pyinstaller.org/) and
[wix](http://wixtoolset.org/). The steps needed to build the code
and assemble it into the installer is automated using a batch
script and can be run as:

```powershell
deploy.bat
```

**Note:** This does not play nicely with the conda environment created above. Update TBD...

To simply generate the executable code without the MSI installer the
following command can be used:

```bash
pyinstaller -y --clean joystick_gremlin.spec
```

This returns a distributable version under `dist/joystick_gremlin`. Build details are stored under `build/joystick_gremlin`.
