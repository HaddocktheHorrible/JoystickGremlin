"""Populates bindings from CSV to current Profile

Column indexes start at 1
Assumes 1 header
vjoy_#-x_axis
vjoy_#-btn_#
axis (match ax.*)
button (match b.*n)

Lines starting in "[" or ";" are ignored. Config entries that do not
relate to key bindings (such as "difficulty"; axis sensitivity and
dead zones; and chat window settings) are ignored.

Since hats are not supported by Joystick Gremlin bindings,
"Pov" entries are bound to VJoy buttons instead.

Optional arguments:

    -m, --device_map <VJoy_ID> <CLoD_ID>
            VJoy ID number and associated CLoD ID string; only one
            pair may be specified per flag; multiple flags may be
            specified
            
    --ignore_unmapped
            joystick devices which have not been mapped to a VJoy ID
            will be ignored; if this is not specified; all unmapped
            joystick devices are reassigned to the first available 
            VJoy device

    --ignore_keyboard
            keyboard assignments found in the config file will NOT
            be imported; if this is not specified, all keyboard
            assignments will be imported to vjoy buttons
                        
Arguments example: 

    To assign bindings from "vJoy_Device-66210FF9" to VJoy 1 and to
    remap all remaining buttons and axes to the first available VJoy:
    
    -m 1 66210FF9
    
    To additionally ignore any keyboard buttons (i.e. those that
    have not been assigned to a secondary device):
    
    -m 1 66210FF9 --ignore_keyboard
                        
"""

import re
import argparse
import gremlin.error

import_filter = "Comma-separated list (*.csv)"
_delimiter = ","
_num_headers = 1
_binding_col = None
_assignment_col = None
_description_col = None

_axis_string_to_id = {
    "x_axis":    1,
    "y_axis":    2,
    "z_axis":    3,
    "x_rot":     4,
    "y_rot":     5,
    "z_rot":     6,
    "dial":      7,
    "slider":    8,
}

def main(file_lines, arg_string):
    """Process passed args, run exporter with passed file contents
    
    :param file_lines Contents of file to import; provided by Joystick Gremlin as list from readlines()
    :param arg_string Optional arguments, parsed by _parse_args
    :return Binding dictionary; to be saved to profile by Joystick Gremlin
    """
    global _binding_col, _assignment_col, _description_col
    
    header = file_lines[_num_headers-1]
    args = _parse_args(arg_string.split())
    _binding_col = _get_column_index(header, args.binding_column)
    _assignment_col = _get_column_index(header, args.assignment_column)
    _description_col = _get_column_index(header, args.description_column)
    
    return _import(file_lines[_num_headers:])

def _get_column_index(header, column_id):
    """Return column index from header string and identifier"""
    if column_id is None:
        return column_id

    try:
        return int(column_id) - 1
    except ValueError:
        pass

    try:
        return header.index(column_id)
    except ValueError:
        pass
    
    raise gremlin.error.ImporterError(("Could not find column '{}'!").format(column_id))

def _parse_args(args):
    """Parse optional arg string
    
    Joystick Gremlin hangs if argparse exists with a write to terminal.
    To avoid this:
    
        1. Set `add_help=False` to invalidate '-h' or '--help' outputs
        2. Use `parser.parse_known_args(args)` to filter for unknown args
        
    Here we also raise an ImporterError if unknown args were passed.
    Although this is not strictly necessary, it to the user's benefit to
    error on a typo rather than silently ignoring it.
    
    param: args argument list from arg_string.split()
    """
    
    parser = argparse.ArgumentParser(usage=__doc__, add_help=False)
    parser.add_argument("binding_column",
                        help="column number for list of bindings"
                        )
    parser.add_argument("assignment_column",
                        help="column number for list of vjoy assignments"
                        )
    parser.add_argument("--description_column",
                        default=None,
                        help="column number for list of descriptions"
                        )
    valid, unknown = parser.parse_known_args(args)
    if unknown:
        msg = ("ArgumentError: unknown argument '{}'"
               ).format(unknown[0])
        raise gremlin.error.ImporterError(msg)
    return valid

def _import(file_lines):
    """Parse file lines into dict entries
    
    :return vjoy_item binding dictionary
    """
    
    found = {}
    for line in file_lines:
        item = _delineated_line2vjoy_item(line)
        if item:
            input_type = next(iter(item))
            if input_type in found.keys():
                found[input_type].update(item[input_type])
            else:
                found.update(item)
    return found

def _delineated_line2vjoy_item(line):
    """Interpret line to get vjoy output
    
    :param delineated line string
    :return vjoy_item dict entry
    """
    
    # parse assignment, binding, and description from csv row
    row = line.split(_delimiter)
    try:
        binding = row[_binding_col].strip()
        assignment = row[_assignment_col].strip().lower()
        if _description_col is not None:
            description = row[_description_col].strip()
        else:
            _description_col = -1 # needed for error checking
            description = ""
    except IndexError:
        last_col = max([_binding_col, _assignment_col, _description_col])
        msg = (("Cannot access column {}! "
                "File only contains {} columns"
               ).format(last_col, len(row)))
        raise gremlin.error.ImporterError(msg)
            
    # return empty if invalid entry
    if not _is_valid_assignment(assignment) \
       or not _is_valid_binding(binding):
        return {}
    
    # get vjoy id
    vjoy_str = assignment.split("-")[0]
    if "vjoy_" in vjoy_str:
        vjoy_id = re.sub("vjoy_","",vjoy_str)
    else:
        vjoy_id = ""
        
    # get input_type
    csv_input = assignment.split("-")[-1]
    if (csv_input in _axis_string_to_id or
        re.findall("^ax",csv_input)):
        input_type = "axis"
    else:
        input_type = "button"
        
    # get input_id
    found_num = re.findall("\d+",csv_input)
    if csv_input in _axis_string_to_id:
        input_id = _axis_string_to_id[csv_input]
    elif found_num:
        input_id = found_num[0]
    else:
        input_id = ""
        
    # assemble item to return
    vjoy_item = {}
    vjoy_item[input_type] = {}
    vjoy_item[input_type][binding] = {
        "device_id": vjoy_id,
        "input_id": input_id,
        "description": description
    }
    return vjoy_item

def _is_valid_assignment(assignment):
    """Returns false if invalid assignment is found"""
    
    if not assignment:
        return False    # empty string -- ignore
    elif re.search("vjoy", assignment.split("-")[-1]) is not None:
        return False    # vjoy given without an input type
    else:
        return True
    
def _is_valid_binding(binding):
    """Returns false if invalid binding is found"""
    
    if not binding:
        return False    # empty string -- ignore
    else:
        return True