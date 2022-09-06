# Importer Plugins

Joystick Gremlin's importer feature allows users to populate VJoy bindings from program configuration files directly to the current profile. This capability is provided through the addition of program-specific importer plugins. Builtin plugins are made available to the user through a dropdown in the importer dialog window. User-made plugins may also be used by manually adding them to the list of know importers (through the "+" icon to the right of the importer selection drop-down) or by placing a copy of the importer within the "importer_plugins" folder under the Joystick Gremlin installation directory.

Plugins are written in python. The rest of this document is intended to help guide users who wish to write their own importer plugins. The builtin `clod-import.py` and `xplane11-import.py` follow similar patterns as described here. The user may wish to "follow along" by opening either file.

## Premise

---

The basic idea an importer plugin script is simple. When the importer is run, its goal is to generate a dictionary of bindings from the selected program config file. These bindings are then passed back to Joystick Gremlin to write to the current profile. Import options may be specified by the user through the use of an argument string, which is similar to typical command-line argument formats.

In order for Joystick Gremlin to be able to interface with all importer plugins, several interface guidelines are established in this document. This includes required functions, input/output format definitions, and other considerations.

## Required Functions

---

The only function strictly required to be in any importer plugin is `main()`. This is called by Joystick Gremlin in order to run the importer. However, for readability it is suggested the following capabilities are added to functions which are called by `main()`:

1. An argument parser - this is needed to parse the argument string for import options
2. An importer function - this should return a binding dictionary

Additional functions may be included as needed to prepare binding entry lines and so on.

## Input Provided by Joystick Gremlin

---

<!-- TODO: update this -->

Three inputs are provided to `main()` by Joystick Gremlin, in the following order:

1. A binding dictionary of copied `BoundVJoy` objects from the current profile
2. The contents of the chosen import file, as reported by python's `readlines()`
3. An argument string provided by the user in the import dialog window

The binding dictionary deserves a bit more explanation than the last two. Every key in the binding dictionary is a keybinding string defined within the current profile. Every item in the dictionary corresponds to a `BoundVJoy` object. Every BoundVJoy object contains the following properties:

- binding       : a unique keybinding string
- vjoy_id       : vjoy id for the associated vjoy device
- input_id      : the associated vjoy input id
- vjoy_guid     : windows guid for the associated vjoy device
- input_type    : a Joystick Gremlin `InputType` object
- description   : a non-unique description string

All the above can be accessed from each BoundVJoy object with standard dot-indexing (i.e. `binding = BoundVJoy.binding`). Typically, only the `vjoy_id`, `input_id`, and `input_type` properties will be needed to update import file lines with new keybindings.

The import file contents are provided to `main()` as the output of python's `readlines()` function. That is, as a list, with one line per entry in that list. Newlines are included at the end of each line.

Finally, user arguments to the importer are included as a single string. This should be split and provided to `argparse` in order to define required (and optional) settings, as needed to make the importer work. Frequently, in-game identifiers for VJoy devices do not match any that are visible to Joystick Gremlin. In this case, the only reasonable way to provide those identifiers to the importer is through the use of user arguments. The arguments string is saved to the current profile to simplify re-import. More information about the use of `argparse` to parse an input string is provided [below](#use-of-argparse).

## Output Expected by Joystick Gremlin

---

<!-- TODO: update this -->

If the importer runs successfully, Joystick Gremlin expects `main()` to return a list of lines to write to file. Depending on the user import options, the import file provided may be overwritten in-place with the new file contents or the user may be given the option to select a new file to write to (see [Template File Filter](#import-file-filter) for additional info). The output from the importer is simply written to file with python's `writelines()` function. Note newlines must be included at the end of each line.

If the importer encounters an error, Joystick Gremlin will throw an exception dialog box and provide a traceback to the user. This is particularly useful when editing and testing new importers using the Joystick Gremlin GUI (see [Debugging](#debugging) below). However, where possible, the author of the importer should try to catch possible errors and raise them as a Joystick Gremlin `ImporterError`. Naturally, this gives the author an opportunity to provide a more user-friendly note about the possible cause. See any of the built-in importers for an example usage.

Note if an error is thrown during importer execution, Joystick Gremlin will continue to run. No changes will be made to the import file, even if the user has chosen to overwrite the file.

## Tips and Best Practices

---

Certain features and quirks to be aware of when creating a new importer are described below.

### Importer Help Display

Joystick Gremlin will display the importer docstring within the importer dialog when an importer is selected. This is updated each time a new importer is selected. The docstring can be defined as usual for a regular python script within the importer.

For user readability, Joystick Gremlin will try to adjust the dosctring word wrap to match the dialog box width. Multiple adjacent docstring lines will be "unwrapped" then re-wrapped based on the dialog box width. In this context, "adjacent" means one non-empty line followed by another non-empty line. The second line must not begin with any form of whitespace or it will not be considered adjacent. The first line may end with any number of spaces -- all will be replaced by a single space when the lines are unwrapped. For example:

```python
"""This will unwrap to  
one line.

This will start a new line. Each bullet 
will be on its own line:
  - Bullet one
  - Bullet two
"""
```

Note paragraph breaks must contain no whitespace to be considered "empty".

### Template File Filter

<!-- TODO: update this -->

To prompt the user for a configuration import file and an output file location, Joystick Gremlin create PyQT `QFileDialog` objects. These support one or more file filters. This allows us to suggest to the user the appropriate file type for the selected importer script. This is enabled in Joystick Gremlin by defining a single `import_filter` variable within the importer. This string defines allowable file extensions for both the import file and import file selection dialogs.

The `import_filter` string must match the format specified by [`QFileDialog`](https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QFileDialog.html#detailed-description); that is an optional file type description followed by one or more file search patterns in parenthesis. Multiple file filters must be separated by two semi-colons. For example:

```python
import_filter = "Text files (*.txt *.ini);;XML files (*.xml)"
```

The order displayed in the `QFileDialog` filter dropdown matches the order entered in the `import_filter` string. Note Joystick Gremlin defines `"All Files (*.*)"` as the default; regardless of the `import_filter` used, the "All Files" option will be available as the last entry in the filter dropdown. If `import_filter` is not defined in the importer script, the "All Files" option will still be shown.

### Use of argparse

As mentioned above, importer-specific options can be specified by the user as POSIX-style input arguments within Joystick Gremlin. These are passed to the importer script as a single string. To parse this string, the importer script should define a parsing scheme using python's `argparse`. This is similar to what one might define for a script to call from the command line, although the author must take a few precautions.

Most importantly, we must prevent argparse from attempting to write to terminal output. This will cause Joystick Gremlin to hang without throwing an error. To avoid this behavior:

1. Remove the default "--help" option by setting `add_help=False` when createing the argparse object
2. Wrap the argument parser execution with a `try ... except` block

The second will catch any errors thrown when arguments are incorrectly formatted. This is particularly useful to raise back to the user. Similarly, it is useful to raise an error when unknown arguments are passed. They can be caught with:

```python
valid, unknown = parser.parse_known_args(arg_string)
```

Finally, the author may find it useful to allow quoted strings in the input arguments. To correctly split over quoted strings, the author may import python's builtin shlex library. The `shlex.split()` function will preserve quoted strings.

### Debugging

The easiest way to debug is to run Joystick Gremlin from source in a python build environment. The author may add breakpoints to their script to monitor variables during execution and so on. See the top-level README for instructions about creating a python environment using conda.

As an alternative, the script writer may open the Joystick Gremlin executable, then run their importer. Joystick Gremlin will report the traceback for any uncaught errors encountered during script execution.

In any case, it is important to know that the importer script is re-loaded every time the "Import" button is pressed or when a new importer is selected. The former is useful for debugging as the script can be edited and run again without having to reload Joystick Gremlin entirely. The latter is mostly useful for editing docstring formatting for proper display in the Importer dialog window.

### Compatibility Considerations

The author should be mindful that any imported python modules must be present within the build environment used to compile Joystick Gremlin. For a full list of available packages, see `conda_env.yaml` in the Joystick Gremlin source code root.
