"""Populates profile bindings from XPlane 11 profile (.prf) file from template.

Optional arguments:

    -m, --device_map <VJoy_ID> <first_AXIS_use_id> <first_BUTN_use_id>
            VJoy ID number and corresponding axis/button start indices 
            within the given .prf file template; each vjoy mapping must 
            include the vjoy id, axis start index, and button start
            index, in that order
            
    --ignore_unmapped
            joystick devices which have not been mapped to a VJoy ID
            will be ignored; if this is not specified; all unmapped
            joystick devices are reassigned to the first available 
            VJoy device

Arguments example: 

    To output VJoy 1 entries from axis 0 and button 0 onwards; VJoy 2 
    entries from axis 10 and button 129; to ignore any bindings set in Joystick 
    Gremlin starting with '?'; and to clear existing bindings from the 
    .prf template file
    
    -m 1 0 0 -m 2 10 129 -i ? -c

Hint: 

    To find the axis/button start index for each vjoy device, manually 
    bind the VJoy X axis and VJoy Button 1 in XPlane 11 in a new, empty profile.
    Save the profile in XPlane 11, then navigate to the corresponding 
    .prf file on disk. Open the .prf file in a text editor, then search for the 
    first non-empty entry binding (for axes, this is any value other than "0"; 
    for buttons, this is any value other than "sim/none/none"). 

    Each entry should look one of the following: 
        "_joy_AXIS_use<AXIS_use_id>"
        "_joy_BUTN_use<BUTN_use_id>"

    You can then enter the <AXIS_use_id> and <BUTN_use_id> as input arguments to 
    this exporter for the VJoy ID used. Repeat the process for all VJoy devices.
    
"""

import re
import argparse
import gremlin.error
from gremlin.common import InputType

template_filter = "XPlane 11 Profile (*.prf)"
_ignore_unmapped = False

# common data for input types
_axis = InputType.JoystickAxis
_butn = InputType.JoystickButton
_type_data = {
    _axis: {
        "vjoy_map": {}, 
        "default": "0", 
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

def main(file_lines, arg_string):
    """Process passed args, run importer with passed file contents
    
    :param file_lines Contents of file to import; provided by Joystick Gremlin as list from readlines()
    :param arg_string Optional arguments, parsed by _parse_args
    :return Binding dictionary; to be saved to profile by Joystick Gremlin
    """
    global _type_data, _ignore_unmapped
    
    try:
        args = _parse_args(arg_string.split())
    except gremlin.error.ImporterError as e:
        raise e
    except:
        msg = "ArgumentError: bad input arguments. Check importer description for details."
        raise gremlin.error.ImporterError(msg)
    
    _ignore_unmapped = args.ignore_unmapped
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
    parser.add_argument("--ignore_unmapped", 
                        action='store_true',
                        help="do not import unmapped joystick devices"
                        )
    valid, unknown = parser.parse_known_args(args)
    if unknown:
        msg = ("ArgumentError: unknown argument '{}'"
               ).format(unknown[0])
        raise gremlin.error.ExporterError(msg)
    return valid

def _import(file_lines):
    """Parse non-commented file lines into dict entries
    
    :return vjoy_item binding dictionary
    """
    
    found = {}
    for line in file_lines:
        item = _xp11_item2vjoy_item(line)
        if item:
            input_type = next(iter(item))
            if input_type in found.keys():
                found[input_type].update(item[input_type])
            else:
                found.update(item)
    return found

def _xp11_item2vjoy_item(xp11_item):
    """Return vjoy item from xplane 11 entry"""
    
    # search for axis or button items
    # todo: use not default in search string
    axis_match = _type_data[_axis]["entry_format"].format(".*", ".*")
    butn_match = _type_data[_butn]["entry_format"].format(".*", ".*")
    
    if   re.match(axis_match, xp11_item):
        vjoy_item = _parse_entry_of_type(xp11_item, _axis)
    elif re.match(butn_match, xp11_item):
        vjoy_item = _parse_entry_of_type(xp11_item, _butn)
    else: # return empty if neither found
        vjoy_item = {}
        
    return vjoy_item

def _parse_entry_of_type(xp11_item, input_type):
    
    # split
    # get binding from second entry
    # get digits at end of first string with re
    # use vjoy dict lookup to get vjoy id
    # enter blank description
    # todo: how to get last input id
    
    return {}

def _remove_commented_items(bound_vjoy_dict):
    """Removes bindings flagged with comment string"""
    cleaned_vjoy_list = {}
    for binding, vjoy_item in bound_vjoy_dict.items():
        if binding[0] not in _ignore_flags:
            cleaned_vjoy_list[binding] = vjoy_item
    return cleaned_vjoy_list

def _validate_map(bound_vjoy_dict):
    """Check all bound vjoy_ids have a mapping"""
    
    # collect all vjoy's from input items
    bound_vjoys = set([i.vjoy_id for i in bound_vjoy_dict.values()])
    
    # collect all vjoys in map
    mapped_vjoys = set()
    for input_type in _type_data:
        mapped_vjoys.update(_type_data[input_type]["vjoy_map"].values())

    # check for missing bound vjoys from map        
    if bound_vjoys - mapped_vjoys:
        msg = ("Mapping error: missing required mapping for VJoy ID's: {}"
              ).format(bound_vjoys - mapped_vjoys)
        raise gremlin.error.ExporterError(msg)
    return bound_vjoy_dict

def _update_entries_of_type(entry_list, bound_vjoy_dict, input_type):
    """Update file lines for given type"""
    
    # find first assignment of correct type in file
    entry_format = _type_data[input_type]["entry_format"]
    entry_match = entry_format.format(".*", ".*")
    line_idx = 0
    while re.match(entry_match, entry_list[line_idx]) is None:
        line_idx += 1
        
    # prep to update lines
    binding_default = _type_data[input_type]["default"]
    binding_match = "(?<=\s).*(?=\n)$"
    item_list = _prepare_bound_items_of_type(bound_vjoy_dict, input_type)
    item_idx = 0
    
    # march over items in order
    while item_idx < len(item_list):
        
        # unpack current item
        binding = item_list[item_idx].binding
        input_id = item_list[item_idx].input_id
        item_match = entry_format.format(input_id, ".*") 
        item_entry = entry_format.format(input_id, binding + "\n") 
        
        # walk over lines until a match for current item is found
        while re.match(item_match, entry_list[line_idx]) is None:
            if re.match(entry_match, entry_list[line_idx]) is None:
                msg = ("Config Error: insufficient {} items in .prf file."
                       ).format(InputType.to_string(input_type))
                raise gremlin.error.ExporterError(msg)
            if _clear_existing:
                entry_list[line_idx] = re.sub(binding_match, binding_default, entry_list[line_idx])
            line_idx += 1
            
        # replace next line with our item
        entry_list[line_idx] = item_entry
        line_idx += 1
        item_idx += 1
        
    # clear remaining entries of type
    if _clear_existing:
        while re.match(entry_match, entry_list[line_idx]) is not None:
            entry_list[line_idx] = re.sub(binding_match, binding_default, entry_list[line_idx])
            line_idx += 1
            
    return entry_list
 
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
    return xp11_items
