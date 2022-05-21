"""Exports to template file
"""

import argparse
import gremlin.error
from gremlin.common import InputType

template_filter = "CLoD Config (*.ini)"
_comment_flags = ["[", ";"]
_ignore_flags = []
_vjoy_map = {}
    
    # 1: "vJoy_Device-66210FF9",
    # 2: "vJoy_Device-A4E92C9",
    # 3: "vJoy_Device-BBF5032F"

_axis_id_to_string = {
    1: "X",
    2: "Y",
    3: "Z",
    4: "RX",
    5: "RY",
    6: "RZ",
    7: "U",
    8: "V",
}

def main(bound_vjoy_dict, template_file, arg_string):
    """Process passed args, run exporter with passed binding list and template
    
    :param bound_vjoy_dict BoundVJoy item dictionary, keyed by binding string; provided by Joystick Gremlin
    :param template_file Config template file contents; provided by Joystick Gremlin
    :param arg_string Optional arguments, parsed by _parse_args
    :return Config file contents with updated bindings; to by saved by Joystick Gremlin
    """
    global _vjoy_map, _ignore_flags
    
    args = _parse_args(arg_string.split())
    _ignore_flags = args.ignore_flag
    for pair in args.device_map:
        _vjoy_map[pair[0]] = "vJoy_Device-%s".format(pair[1])
    
    return _export(bound_vjoy_dict, template_file)

def _parse_args(args):
    """Parse optional arg string"""
    parser = argparse.ArgumentParser(description="Create IL-2 CLoD config file from template")
    parser.add_argument("-m", "--device_map", nargs=2, action='append', 
                        metavar=('VJOY_ID','CLOD_ID'), help="vjoy id and associated CLoD id")
    # todo: validate map as <int str> pair
    # todo: strip "vJoy-Device-" from CLoD ID, if passed
    parser.add_argument("-i", "--ignore_flag", type=str, nargs='?', action='append', default=["#"],
                        type=lambda x: x if len(x) <=1 else False, # limit flag to one char at a time
                        help="binding assignments starting with IGNORE_FLAG are ignored")
    
    return parser.parse_args(args)

def _export(bound_vjoy_dict, template_file):
    
    oldfile = template_file
    newfile = []
    
    bound_vjoy_dict = _remove_commented_items(bound_vjoy_dict)
    
    # overwrite old bindings in-place
    for line in oldfile:
        line = line.strip()
        if line and line[0] not in _comment_flags:
            binding = line.split("=")[-1].strip()
            assignment = line.split("=")[0].strip()
            if binding in bound_vjoy_dict.keys():
                bound_item = bound_vjoy_dict[binding]
                line = _vjoy_item2clod_item(bound_item)
                bound_vjoy_dict.pop(binding)
            elif assignment.split("+")[0] in _vjoy_map.values():
                # remove old assignment from output data
                line = "; =%s".format(binding)
        newfile.append(line)
    
    # append unsorted bindings to file
    newfile.append(["[Unsorted Gremlin Bindings]\n"])
    for bound_item in bound_vjoy_dict.values():
        newfile.append(_vjoy_item2clod_item(bound_item))
        
    return newfile

def _remove_commented_items(bound_vjoy_dict):
    """Removes bindings flagged with comment string"""
    cleaned_vjoy_list = {}
    for binding, vjoy_item in bound_vjoy_dict.items():
        if binding[0] not in _ignore_flags:
            cleaned_vjoy_list[binding] = vjoy_item
    return cleaned_vjoy_list
        
def _vjoy_item2clod_item(bound_item):
    """Return vjoy to string for clod
    
    :param bound_item BoundVJoy instance to write
    """
    # get correct device ID as recognized by CLoD
    try:
        device_str = _vjoy_map[bound_item.vjoy_id]
    except KeyError:
        msg = ("CLoD device ID not defined for vJoy Device %d!"
               "\nSpecify vjoy to CLoD mapping with arg \"-m %d <CLoD-vJoy_Device-ID>\" "
               "\nHint: find CLoD-vJoy_Device-ID from CLoD-generated \"confuser.ini\" config file."
              ).format(bound_item.vjoy_id, bound_item.vjoy_id)
        raise gremlin.error._ExporterError(msg)
    
    # get correct axis/button naming for clod
    input_type = bound_item.input_type
    if input_type == InputType.JoystickAxis:
        input_str = _axis_id_to_string(bound_item.input_id)
    elif input_type == InputType.JoystickButton:
        input_str = "Key%d".format(bound_item.input_id - 1)
    else:
        msg = "CLoD _export not defined for outputs of type \"%s\"".format(InputType.to_string(input_type))
        raise gremlin.error._ExporterError(msg)
    
    return  "%s+%s=%s".format(device_str,input_str,bound_item.binding)
