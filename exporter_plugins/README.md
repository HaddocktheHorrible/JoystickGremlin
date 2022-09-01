# Exporter Plugins

Joystick Gremlin's exporter feature allows users to write VJoy bindings from the current profile directly to program configuration files. This capability is provided through the addition of program-specific exporter plugins. Builtin plugins are made available to the user through a dropdown in the exporter dialog window. User-made plugins may also be used by manually adding them to the list of know exporters (through the "+" icon to the right of the exporter selection drop-down) or by placing a copy of the exporter within the "exporter_plugins" folder under the Joystick Gremlin installation directory.

Plugins are written in python. The rest of this document is intended to help guide users who wish to write their own exporter plugins. The builtin `clod-export.py` and `xplane11-export.py` follow similar patterns as described here. The user may wish to "follow along" by opening either file.

## Premise

---

The basic idea an exporter plugin script is simple. When the exporter is run, its goal is to update the contents of a template file with bindings from the current profile. The updated file contents are then returned to Joystick Gremlin to write to file. Output options may be specified by the user through the use of an argument string, which is similar to typical command-line argument formats.

In order for Joystick Gremlin to be able to interface with all exporter plugins, several interface guidelines are established in this document. This includes required functions, input/output format definitions, and other considerations.

## Required Functions

---

The only function strictly required to be in any exporter plugin is `main()`. This is called by Joystick Gremlin in order to run the exporter. However, for readability it is suggested the following capabilities are added to functions which are called by `main()`:

1. An argument parser - this is needed to parse the argument string for export options
2. An exporter function - this should return the modified template file

Additional functions may be included as needed to prepare binding entry lines and so on.

## Input Provided by Joystick Gremlin

---

Three inputs are provided to `main()` by Joystick Gremlin, in the following order:

1. A binding dictionary of copied `BoundVJoy` objects from the current profile
2. The contents of the chosen template file, as reported by python's `readlines()`
3. An argument string provided by the user in the export dialog window

The binding dictionary deserves a bit more explanation than the last two. Every key in the binding dictionary is a keybinding string defined within the current profile. Every item in the dictionary corresponds to a `BoundVJoy` object. Every BoundVJoy object contains the following properties:

- binding       : a unique keybinding string
- vjoy_id       : vjoy id for the associated vjoy device
- input_id      : the associated vjoy input id
- vjoy_guid     : windows guid for the associated vjoy device
- input_type    : a Joystick Gremlin `InputType` object
- description   : a non-unique description string

All the above can be accessed from each BoundVJoy object with standard dot-indexing (i.e. `binding = BoundVJoy.binding`). Typically, only the `vjoy_id`, `input_id`, and `input_type` properties will be needed to update template file lines with new keybindings.

The template file contents are provided to `main()` as the output of python's `readlines()` function. That is, as a list, with one line per entry in that list. Newlines are included at the end of each line.

Finally, user arguments to the exporter are included as a single string. This should be split and provided to `argparse` in order to define required (and optional) settings, as needed to make the exporter work. Frequently, in-game identifiers for VJoy devices do not match any that are visible to Joystick Gremlin. In this case, the only reasonable way to provide those identifiers to the exporter is through the use of user arguments. The arguments string is saved to the current profile to simplify re-export. More on the use of `argparse` to parse an input string later in this guide.

## Output Expected by Joystick Gremlin



## Tips and Best Practices

### Template File Filter

template_filter

### Use of argparse

wrap in try except to avoid hangs
use shlex for quoted args

### Debugging

reloaded on each export

### Compatibility Considerations

use of import modules