"""Populates bindings from IL-2 CLoD config file to current Profile

Optional arguments:

    -m, --device_map <VJoy_ID> <CLoD_ID>
            VJoy ID number and associated CLoD ID string; only one
            pair may be specified per flag; multiple flags may be
            specified

    -i, --ignore_flag <ignore_flag>
            binding assignments starting with IGNORE_FLAG are ignored; 
            ignored bindings are not listed in the output file; 
            multiple flags may be specified, but each flag may only 
            consist of one character; default = '#'
                        
Arguments example: 

    To register VJoy 1 as "vJoy_Device-66210FF9", VJoy 2 as 
    "vJoy_Device-A4E92C9", and to ignore any bindings set in Joystick 
    Gremlin starting with '#':
    
    -m 1 66210FF9 -m 2 A4E92C9 -i #
                        
Hint: 

    To find the CLoD ID for each VJoy device, manually bind one VJoy 
    output in CLoD. CLoD will report VJoy device bindings in the format:
    
    "vJoy_Device-<CLoD_ID>+Key#=<binding>"
    
    You may then register that CLoD_ID with its corresponding VJoy_ID as 
    described above.
    
"""

import argparse
import gremlin.error

import_filter = "CLoD Config (*.ini)"
_comment_flags = ["[", ";"]
_ignore_flags = []
_vjoy_map = {}

_axis_string_to_id = {
    "AXE_X":    1,
    "AXE_Y":    2,
    "AXE_Z":    3,
    "AXE_RX":   4,
    "AXE_RY":   5,
    "AXE_RZ":   6,
    "AXE_U":    7,
    "AXE_V":    8,
}

class AppendMapPair(argparse.Action):
    """Validates vjoy_id, clod_id pair is well-formed; appends to existing list, if any"""
    def __call__(self, parser, namespace, values, option_string=None):
        
        # validate
        vjoy_id, clod_id = values
        try:
            vjoy_id = int(vjoy_id)
        except ValueError:
            raise gremlin.error.ImporterError((
                "Invalid VJoy_ID argument: '{}' is not a valid integer"
                ).format(vjoy_id))
        clod_id = clod_id.replace("vJoy_Device-","")
        
        # append and return
        items = getattr(namespace, self.dest) or []
        items.append([vjoy_id, clod_id])
        setattr(namespace, self.dest, items)

def main(file_lines, arg_string):
    """Process passed args, run exporter with passed file contents
    
    :param file_lines Contents of file to import; provided by Joystick Gremlin as list from readlines()
    :param arg_string Optional arguments, parsed by _parse_args
    :return Binding dictionary; to be saved to profile by Joystick Gremlin
    """
    global _vjoy_map, _ignore_flags
    
    args = _parse_args(arg_string.split())
    _ignore_flags = args.ignore_flag
    for vjoy_id, clod_id in args.device_map:
        _vjoy_map["vJoy_Device-{}".format(clod_id)] = vjoy_id
    
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
                        metavar=('VJOY_ID','CLOD_ID'), 
                        help="vjoy id and associated CLoD id"
                        )
    parser.add_argument("-i", "--ignore_flag", 
                        nargs='?', 
                        action='append', default=["#"],
                        type=lambda x: x if len(x) <=1 else False, # limit flag to one char at a time
                        help="binding assignments starting with IGNORE_FLAG are ignored"
                        )
    valid, unknown = parser.parse_known_args(args)
    if unknown:
        msg = ("ArgumentError: unknown argument '{}'"
               ).format(unknown[0])
        raise gremlin.error.ImporterError(msg)
    return valid

def _import(file_lines):
    
    
    # todo: ignore non-binding lines in ini file
    # most have one or more numbers in 'binding' field xxx=## ## ##
    # BOB are just keywords in the "assignment" field
    # Last Focus are keywords in the "binding" field
    # chat window has a ":" in the "assignment" field
    
    found = {}
    for line in file_lines:
        if line and line.strip()[0] not in _comment_flags:
            found.update(_clod_item2vjoy_item(line))
    return found

def _clod_item2vjoy_item(clod_item):
    """Interpret clod entry to vjoy output
    
    :param clod_item CLoD .ini line to parse
    """
    assignment = clod_item.split("=")[0].strip()
    binding = clod_item.split("=")[-1].strip()
    clod_dev = assignment.split("+")[0]
    clod_input = assignment.split("+")[-1]
    
    # get vjoy_id
    # todo: make option to disable grabbing unknown vjoys
    if clod_dev in _vjoy_map:
        vjoy_id = _vjoy_map[clod_dev]
    else:
        vjoy_id = ""
    
    # get input_type and id
    # todo: make option to disable binding key assignments
    if clod_input in _axis_string_to_id:
        input_type = "axis"
        input_id = _axis_string_to_id[clod_input]
    elif "Key" in clod_input:
        input_type = "button"
        input_id = int(clod_input.split("Key")[-1])
    else:
        input_type = "button"
        input_id = ""
        
    # assemble return
    vjoy_item = {}
    vjoy_item[input_type] = {}
    vjoy_item[input_type][binding] = {
        "device_id": vjoy_id,
        "input_id": input_id,
        "description": ""
    }
    return vjoy_item
