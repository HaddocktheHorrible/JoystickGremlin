"""Populates profile bindings to XPlane 11 profile (.prf) file from template.


# TODO: update

Optional arguments:

    -m, --device_map <VJoy_ID> <first_AXIS_use_id> <first_BUTN_use_id>
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

import re
import argparse
import gremlin.error
from gremlin.common import InputType

template_filter = "XPlane 11 Profile (*.prf)"
_comment_flags = ["[", ";"]
_ignore_flags = []
_clear_existing = False

_axis = InputType.JoystickAxis
_butn = InputType.JoystickButton

_type_data = {
    _axis: {
        "vjoy_map": {}, 
        "default": 0, 
        "entry_format": "_joy_AXIS_use{} {}"
    },
    _butn: {
        "vjoy_map": {}, 
        "default": "sim/none/none", 
        "entry_format": "_joy_BUTN_use{} {}"
    },
}

class AppendMapPair(argparse.Action):
    """Validates vjoy_id, clod_id pair is well-formed; appends to existing list, if any"""
    def __call__(self, parser, namespace, values, option_string=None):
        
        # validate
        for i in values:
            try:
                i = int(i)
            except ValueError:
                raise gremlin.error.ExporterError((
                    "Invalid map argument: '{}' is not a valid integer"
                    ).format(i))
        
        # append and return
        vjoy_id, axis_id, butn_id = values
        items = getattr(namespace, self.dest) or []
        items.append([vjoy_id, axis_id, butn_id])
        setattr(namespace, self.dest, items)

def main(bound_vjoy_dict, template_file, arg_string):
    """Process passed args, run exporter with passed binding list and template
    
    :param bound_vjoy_dict BoundVJoy item dictionary, keyed by binding string; provided by Joystick Gremlin
    :param template_file Config template file contents; provided by Joystick Gremlin as list from readlines()
    :param arg_string Optional arguments, parsed by _parse_args
    :return Config file contents list with updated bindings; to be saved by Joystick Gremlin with writelines()
    """
    global _type_data, _ignore_flags, _clear_existing
    
    args = _parse_args(arg_string.split())
    _ignore_flags = args.ignore_flag
    _clear_existing = args.clear_existing
    if args.device_map is not None:
        for vjoy_id, axis_id, butn_id in args.device_map:
            _type_data[_axis]["vjoy_map"][int(axis_id)] = int(vjoy_id)
            _type_data[_butn]["vjoy_map"][int(butn_id)] = int(vjoy_id)
    return _export(bound_vjoy_dict, template_file)

def _parse_args(args):
    """Parse optional arg string
    
    Joystick Gremlin hangs if argparse exists with a write to terminal.
    To avoid this:
    
        1. Set `add_help=False` to invalidate '-h' or '--help' outputs
        2. Use `parser.parse_known_args(args)` to filter for unknown args
        
    Here we also raise an ExporterError if unknown args were passed.
    Although this is not strictly necessary, it to the user's benefit to
    error on a typo rather than silently ignoring it.
    
    param: args argument list from arg_string.split()
    """
    
    parser = argparse.ArgumentParser(usage=__doc__, add_help=False)
    parser.add_argument("-m", "--device_map", 
                        nargs=3, 
                        action=AppendMapPair, 
                        metavar=('VJOY_ID','AXIS_ID', 'BUTN_ID'), 
                        help="vjoy id and associated first axis and button ids"
                        )
    parser.add_argument("-i", "--ignore_flag", 
                        nargs='?', 
                        action='append', default=["#"],
                        type=lambda x: x if len(x) <=1 else False, # limit flag to one char at a time
                        help="binding assignments starting with IGNORE_FLAG are ignored"
                        )
    parser.add_argument("-c", "--clear_existing", 
                        action="store_true",
                        help="will reset unspecified axis and button bindings in file to default"
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
    
    bound_vjoy_dict = _remove_commented_items(bound_vjoy_dict)
    
    # todo: check all bound vjoy_ids have a mapped axis or button
    
    # find first axis assignment in file
    entry_default = _type_data[_axis]["default"]
    entry_format = _type_data[_axis]["entry_format"]
    entry_match = entry_format.format(".*", ".*")
    line_idx = 0
    while re.match(entry_match, oldfile[line_idx]) is None:
        newfile.append(oldfile[line_idx] + "\n")
        line_idx += 1
        
    axis_items = _prepare_bound_items_of_type(bound_vjoy_dict, _axis)
    item_idx = 0
    
    
    # march over items
    while item_idx < len(axis_items):
        binding = axis_items[item_idx].binding
        input_id = axis_items[item_idx].input_id
        item_entry = entry_format.format(input_id, binding) 
        item_match = entry_format.format(input_id, ".*") 
        
        # walk over lines until a match for current item is found
        while re.match(item_match, oldfile[line_idx]) is None:
            if re.match(entry_match, oldfile[line_idx]) is None:
                msg = ("Config Error: insufficient {} items in .prf file."
                       ).format(InputType.to_string(_axis))
                raise gremlin.error.ExporterError(msg)
            if _clear_existing:
                new_line = re.sub("(?<=\s).*$", entry_default, oldfile[line_idx])
            else:
                new_line = oldfile[line_idx]
            newfile.append(new_line + "\n")
            line_idx += 1
            
        # replace next line with our item
        newfile.append(item_entry + "\n")
        line_idx += 1
        item_idx += 1
        
    # clear remaining lines
    if _clear_existing:
        while re.match(entry_match, oldfile[line_idx]):
            new_line = re.sub("(?<=\s).*$", entry_default, oldfile[line_idx])
            newfile.append(new_line + "\n")
            line_idx += 1
            
    # todo: repeat with button
    
    return newfile

def _prepare_bound_items_of_type(bound_vjoy_dict, input_type):
    """Group and sort bindings for given type into order expected by XPlane"""
    
    vjoy_items = [ item for item in bound_vjoy_dict.values() if item.input_type == input_type ]
    xp11_items = _vjoy_items_to_xp11_items(vjoy_items, _type_data[input_type]["vjoy_map"])
    
    return xp11_items
        
def _vjoy_items_to_xp11_items(all_vjoy_items, vjoy_map):
    """Prepare item list for XPlane 11 import"""
    
    # sort items into order for xplane 11 prf file
    # update item input_ids to match xplane 11 numbering
    xp11_items = []
    for xp11_idx in sorted(vjoy_map):
        vjoy_id = vjoy_map[xp11_idx]
        vjoy_items = [ i for i in all_vjoy_items if i.vjoy_id == vjoy_id ]
        vjoy_items = sorted(vjoy_items, key=lambda x: x.input_id)
        for item in vjoy_items:
            item.input_id += (xp11_idx - 1)
        xp11_items += vjoy_items

def _remove_commented_items(bound_vjoy_dict):
    """Removes bindings flagged with comment string"""
    cleaned_vjoy_list = {}
    for binding, vjoy_item in bound_vjoy_dict.items():
        if binding[0] not in _ignore_flags:
            cleaned_vjoy_list[binding] = vjoy_item
    return cleaned_vjoy_list
