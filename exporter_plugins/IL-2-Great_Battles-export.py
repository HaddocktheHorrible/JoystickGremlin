"""Populates profile bindings to IL-2: Great Battles (i.e. Battle of X... BoX) actions file from template.

Optional arguments:

    -m, --device_map <VJoy_ID> <BoX_ID>
            VJoy ID number and associated BoX ID string; only one
            pair may be specified per flag; multiple flags may be
            specified

    -i, --ignore_flag <ignore_flag>
            binding assignments starting with IGNORE_FLAG are ignored; 
            ignored bindings are not listed in the output file; 
            multiple flags may be specified, but each flag may only 
            consist of one character; default = '#'
            
    --remove_unmapped
            only print "joy" entries from template file to new actions
            file if they are mapped to a vjoy device
            
    --remove_mouse
            do not print mouse assignments from template file to new
            actions file
            
    --remove_keyboard
            do not print keyboard-only assignments in template file to
            new actions file; "key+mouse" and "key+joy" assignments are
            still printed unless "--remove_mouse" and "--remove_unmapped"
            are also flagged

Arguments example: 

    To register VJoy 1 as "joy1", VJoy 2 as 
    "joy2", and to ignore any bindings set in Joystick 
    Gremlin starting with '#':

    -m 1 1 -m 2 2 -i #

Tips:

(1) The vjoy to BoX_ID mappings may be viewed and edited from:

    'profiles-install/devices.txt'

    within your IL-2: Great Battles installation directory.

(2) The output '.actions' file must be saved under:

    'profiles-install/custom/'

    within your IL-2: Great Battles installation directory.

"""

import argparse
import gremlin.error
from gremlin.common import InputType

template_filter = "BoX Actions (*.actions)"
_comment_flags = ["/", "&"]
_ignore_flags = []
_vjoy_map = {}
_remove_unmapped = False
_remove_keyboard = False
_remove_mouse = False

_axis_id_to_string = {
    1: "axis_x",
    2: "axis_y",
    3: "axis_z",
    4: "axis_w",
    5: "axis_s",
    6: "axis_t",
    7: "axis_p",
    8: "axis_q",
}

class AppendMapPair(argparse.Action):
    """Validates vjoy_id, box_id pair is well-formed; appends to existing list, if any"""
    def __call__(self, parser, namespace, values, option_string=None):
        
        # validate
        vjoy_id, box_id = values
        try:
            vjoy_id = int(vjoy_id)
        except ValueError:
            raise gremlin.error.ExporterError((
                "Invalid VJoy_ID argument: '{}' is not a valid integer"
                ).format(vjoy_id))
        box_id = box_id.replace("vJoy_Device-","")
        
        # append and return
        items = getattr(namespace, self.dest) or []
        items.append([vjoy_id, box_id])
        setattr(namespace, self.dest, items)

def main(bound_vjoy_dict, template_file, arg_string):
    """Process passed args, run exporter with passed binding list and template
    
    :param bound_vjoy_dict BoundVJoy item dictionary, keyed by binding string; provided by Joystick Gremlin
    :param template_file Config template file contents; provided by Joystick Gremlin as list from readlines()
    :param arg_string Optional arguments, parsed by _parse_args
    :return Config file contents list with updated bindings; to be saved by Joystick Gremlin with writelines()
    """
    global _vjoy_map, _ignore_flags
    global _remove_unmapped, _remove_keyboard, _remove_mouse

    
    try:
        args = _parse_args(arg_string.split())
    except gremlin.error.ExporterError as e:
        raise e
    except:
        msg = "ArgumentError: bad input arguments. Check exporter description for details."
        raise gremlin.error.ExporterError(msg)
    
    _ignore_flags = args.ignore_flag
    _remove_unmapped = args.remove_unmapped
    _remove_keyboard = args.remove_keyboard
    _remove_mouse = args.remove_mouse
    if args.device_map is not None:
        for vjoy_id, box_id in args.device_map:
            _vjoy_map[vjoy_id] = "joy{}".format(box_id)
    
    return _export(bound_vjoy_dict, template_file)

def _parse_args(args):
    """Parse optional arg string
    
    Joystick Gremlin hangs if argparse exists with a write to terminal.
    To avoid this:
    
        1. Set 'add_help=False' to invalidate '-h' or '--help' outputs
        2. Use 'parser.parse_known_args(args)' to filter for unknown args
        
    Here we also raise an ExporterError if unknown args were passed.
    Although this is not strictly necessary, it to the user's benefit to
    error on a typo rather than silently ignoring it.
    
    param: args argument list from arg_string.split()
    """
    
    parser = argparse.ArgumentParser(usage=__doc__, add_help=False)
    parser.add_argument("-m", "--device_map", 
                        nargs=2, 
                        action=AppendMapPair, 
                        metavar=('VJOY_ID','BoX_ID'), 
                        help="vjoy id and associated BoX id"
                        )
    parser.add_argument("-i", "--ignore_flag", 
                        nargs='?', 
                        action='append', default=["#"],
                        type=lambda x: x if len(x) <=1 else False, # limit flag to one char at a time
                        help="binding assignments starting with IGNORE_FLAG are ignored"
                        )
    parser.add_argument("--remove_unmapped", 
                        action='store_true',
                        help="delete unmapped joy devices from template file"
                        )
    parser.add_argument("--remove_keyboard", 
                        action='store_true',
                        help="delete keyboard bindings from template file"
                        )
    parser.add_argument("--remove_mouse", 
                        action='store_true',
                        help="delete mouse bindings from template file"
                        )
    valid, unknown = parser.parse_known_args(args)
    if unknown:
        msg = ("ArgumentError: unknown argument '{}'"
               ).format(unknown[0])
        raise gremlin.error.ExporterError(msg)
    return valid

def _export(bound_vjoy_dict, template_file):
    
    oldfile = template_file
    newfile = []
    written = []
    
    bound_vjoy_dict = _remove_commented_items(bound_vjoy_dict)
    
    # overwrite old bindings in-place
    # all commented lines get written as-is
    # when a known binding is found, the vjoy binding is inserted first
    #   subsequent valid lines of same binding have their description stripped
    #   subsequent invalid lines of same binding are removed
    # valid lines are retained as-is if no vjoy binding exists
    # invalid lines are printed with their assignment stripped if no vjoy binding exists
    for line in oldfile:
        line = line.strip()
        if line and line[0] not in _comment_flags:
            binding = line.split(",")[0].strip()
            valid_existing, line = _clear_invalid_assignment(line)
            if binding in bound_vjoy_dict.keys():
                bound_item = bound_vjoy_dict[binding]
                bound_vjoy_dict.pop(binding)
                if valid_existing:
                    line = _vjoy_item2box_item(bound_item) + "\n" \
                         + line.split("//")[0].strip()
                else:
                    line = _vjoy_item2box_item(bound_item)
                written.append(binding)
            elif binding in written:
                if valid_existing:
                    line = line.split("//")[0].strip()
                else:
                    continue # don't write invalid line if a prior binding line exists
        newfile.append(line + "\n")
            
    # append unsorted bindings to file
    newfile.append("\n// Unsorted Gremlin Bindings\n")
    for bound_item in bound_vjoy_dict.values():
        newfile.append(_vjoy_item2box_item(bound_item) + "\n")
        
    return newfile

def _clear_invalid_assignment(line):
    # return line with assignment cleared if that assignment is invalid
    # otherwise return original line
    split = line.split(",")
    assignment = split[1].strip()
    cleared =  "{:<50}{:<50}{}".format(split[0].strip()+",",",",split[-1].strip())
    if any(joy in assignment for joy in _vjoy_map.values()):
        return False, cleared
    elif "joy" in assignment and not _remove_unmapped:
        return True, line
    elif "mouse" in assignment and not _remove_mouse:
        return True, line
    elif "key" in assignment and not _remove_keyboard:
        return True, line
    else:
        return False, cleared

def _remove_commented_items(bound_vjoy_dict):
    """Removes bindings flagged with comment string"""
    cleaned_vjoy_list = {}
    for binding, vjoy_item in bound_vjoy_dict.items():
        if binding[0] not in _ignore_flags:
            cleaned_vjoy_list[binding] = vjoy_item
    return cleaned_vjoy_list
        
def _vjoy_item2box_item(bound_item):
    """Return vjoy to string for box
    
    :param bound_item BoundVJoy instance to write
    """
    # get correct device ID as recognized by BoX
    try:
        device_str = _vjoy_map[bound_item.vjoy_id]
    except KeyError:
        msg = ("Missing device_map argument: "
               "BoX_ID not defined for vJoy Device {:d}"
              ).format(bound_item.vjoy_id)
        raise gremlin.error.ExporterError(msg)
    
    # get correct axis/button naming for box
    input_type = bound_item.input_type
    if input_type == InputType.JoystickAxis:
        input_str = _axis_id_to_string[bound_item.input_id]
    elif input_type == InputType.JoystickButton:
        input_str = "b{:d}".format(bound_item.input_id - 1)
    else:
        msg = ("Invalid binding: "
               "BoX export not defined for outputs of type '{}'"
              ).format(InputType.to_string(input_type))
        raise gremlin.error.ExporterError(msg)
    
    # assemble line with consistent spacing
    assignment = device_str + "_" + input_str
    line = "{:<50}{:<50}{}|".format(bound_item.binding+",",assignment+",","0")
    if bound_item.description:
        line = line + " // " + bound_item.description
    return line

