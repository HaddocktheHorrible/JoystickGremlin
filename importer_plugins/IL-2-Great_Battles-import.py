"""Populates bindings from IL-2: Great Battles (i.e. Battle of X... BoX) config file to current Profile

Lines starting in "&" or "/" are ignored. Axis inversions as ignored.

Since hats are not supported by Joystick Gremlin bindings,
"Pov" entries are bound to VJoy buttons instead.

Where duplicate binding lines exist, only the last assignment is kept. 
Use the "ignore" optional arguments if specific vjoy binding assignments
are desired. Regardless of "ignore" arguments, the last non-empty binding
description is always kept. This preserves binding descriptions for the
default BoX .actions file, where only the first entry in a block of duplicate
bindings includes the binding description.

Optional arguments:

    -m, --device_map <VJoy_ID> <BoX_id>
            VJoy ID number and associated BoX ID string; only one
            pair may be specified per flag; multiple flags may be
            specified
            
    --ignore_unmapped
            joystick devices which have not been mapped to a VJoy ID
            will be ignored; if this is not specified, all unmapped
            joystick devices are reassigned to the first available 
            VJoy device

    --ignore_keyboard
            keyboard assignments found in the actions file will NOT
            be imported; if this is not specified, all keyboard
            assignments will be imported to vjoy buttons

    --ignore_mouse
            mouse assignments found in the actions file will NOT
            be imported; if this is not specified, mouse button
            assignments will be imported to vjoy buttons and
            mouse axes will be imported vjoy axes

Arguments example: 

    To assign bindings from "joy1" to VJoy 1 and to
    remap all remaining buttons and axes to the first available VJoy:
    
    -m 1 1
    
    To additionally ignore any keyboard buttons (i.e. those that
    have not been assigned to a secondary device):
    
    -m 1 1 --ignore_keyboard
                        
"""

import shlex
import argparse
import gremlin.error

import_filter = "BoX Custom Actions (*.actions)"
_comment_flags = ["/", "&"]
_ignore_keyboard = False
_ignore_unmapped = False
_ignore_mouse = False
_vjoy_map = {}

_axis_string_to_id = {
    "axis_x":   1,
    "axis_y":   2,
    "axis_z":   3,
    "axis_w":   4,
    "axis_s":   5,
    "axis_t":   6,
    "axis_p":   7,
    "axis_q":   8,
}

class AppendMapPair(argparse.Action):
    """Validates vjoy_id, box_id pair is well-formed; appends to existing list, if any"""
    def __call__(self, parser, namespace, values, option_string=None):
        
        # validate
        vjoy_id, box_id = values
        try:
            vjoy_id = int(vjoy_id)
        except ValueError:
            raise gremlin.error.ImporterError((
                "Invalid VJoy_ID argument: '{}' is not a valid integer"
                ).format(vjoy_id))
        box_id = box_id.replace("joy","")
        
        # append and return
        items = getattr(namespace, self.dest) or []
        items.append([vjoy_id, box_id])
        setattr(namespace, self.dest, items)

def main(file_lines, arg_string):
    """Process passed args, run importer with passed file contents
    
    :param file_lines Contents of file to import; provided by Joystick Gremlin as list from readlines()
    :param arg_string Optional arguments, parsed by _parse_args
    :return Binding dictionary; to be saved to profile by Joystick Gremlin
    """
    global _vjoy_map, _ignore_keyboard, _ignore_unmapped, _ignore_mouse
    
    try:
        args = _parse_args(shlex.split(arg_string))
    except gremlin.error.ImporterError as e:
        raise e
    except:
        msg = "ArgumentError: bad input arguments. Check importer description for details."
        raise gremlin.error.ImporterError(msg)
    
    _ignore_mouse = args.ignore_mouse
    _ignore_keyboard = args.ignore_keyboard
    _ignore_unmapped = args.ignore_unmapped
    if args.device_map is not None:
        for vjoy_id, box_id in args.device_map:
            _vjoy_map["joy{}".format(box_id)] = vjoy_id
    
    return _import(file_lines)

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
    parser.add_argument("-m", "--device_map", 
                        nargs=2, 
                        action=AppendMapPair, 
                        metavar=('VJOY_ID','BoX_id'), 
                        help="vjoy id and associated BoX id"
                        )
    parser.add_argument("--ignore_unmapped", 
                        action='store_true',
                        help="do not import unmapped joystick devices"
                        )
    parser.add_argument("--ignore_keyboard", 
                        action='store_true',
                        help="do not import keyboard assignments"
                        )
    parser.add_argument("--ignore_mouse", 
                        action='store_true',
                        help="do not import mouse assignments"
                        )
    valid, unknown = parser.parse_known_args(args)
    if unknown:
        msg = ("ArgumentError: unknown argument '{}'"
               ).format(unknown[0])
        raise gremlin.error.ImporterError(msg)
    return valid

def _import(file_lines):
    """Parse non-commented file lines into dict entries
    
    :return vjoy_item binding dictionary
    """
    
    # since the default .actions file leaves duplicate binding descriptions empty
    # in addition to finding bindings, we record all descriptions found;
    # if a given binding has no description, we try to fill it from 
    # known descriptions; the last non-empty description for a duplicate binding is used
    
    found = {}
    known_descriptions = {}
    for line in file_lines:
        if line.strip() and line.strip()[0] not in _comment_flags:
            item, new_description = _box_item2vjoy_item(line)
            if new_description:
                known_descriptions.update(new_description)
            if item:
                input_type = next(iter(item))
                binding = next(iter(item[input_type]))
                try: # replace an empty description with a known description
                    item[input_type][binding]["description"] = known_descriptions[binding]
                except:
                    pass
                if input_type in found.keys():
                    found[input_type].update(item[input_type])
                else:
                    found.update(item)
    return found

def _box_item2vjoy_item(box_item):
    """Interpret BoX entry to vjoy output
    
    :param box_item BoX .actions line to parse
    :return vjoy_item dict entry
    """
    
    # parse line entries
    binding = box_item.split(",")[0].strip()
    assignment = box_item.split(",")[1].strip()
    try:
        description = box_item.split("//")[1].strip()
        new_description = {binding: description}
    except: # if no description present on line, leave blank
        description = "" 
        new_description = {}
    
    # if inc/dec delimiter present, treat as keyboard axis
    if "/" in assignment:
        assignment = "key_axis"
    
    # check for multi-input chords
    # keep second if "axis" is present, else keep the first
    chord_delimiter = "+"
    if chord_delimiter in assignment:
        [a,b] = assignment.split(chord_delimiter)
        if "axis" in b:
            assignment = b
        else:
            assignment = a
    
    # parse assignment into device and input
    box_dev = assignment.split("_")[0]
    box_input = assignment.replace(box_dev+"_","") # use this to capture 'axis_id'
    
    # get vjoy_id
    if box_dev in _vjoy_map:
        vjoy_id = _vjoy_map[box_dev]
    elif not _ignore_unmapped:
        vjoy_id = ""
    else:
        return None, new_description
    
    # short-circuit keyboard if ignored
    if _ignore_keyboard and box_dev == "key":
        return None, new_description
    
    # short-circuit mouse if ignored
    if _ignore_mouse and box_dev == "mouse":
        return None, new_description
    
    # get input_type and id
    if box_dev == "key" or box_dev == "mouse":
        input_id = ""
        if "axis" in box_input:
            input_type = "axis"
        else:
            input_type = "button"
    else: # must be joystick
        if box_input in _axis_string_to_id:
            input_type = "axis"
            input_id = _axis_string_to_id[box_input]
        elif "axis" in box_input:
            input_type = "axis"
            input_id   = ""
        elif "b" in box_input:
            input_type = "button"
            input_id = int(box_input.strip("b")) + 1
        elif "pov" in box_input:
            input_type = "button"
            input_id = "" # bindings don't support hats, so assign to button
        else:
            return None, new_description # unknown entry -- skip
            
    # assemble return
    vjoy_item = {}
    vjoy_item[input_type] = {}
    vjoy_item[input_type][binding] = {
        "input_id": input_id,
        "device_id": vjoy_id,
        "description": description
    }
    return vjoy_item, new_description