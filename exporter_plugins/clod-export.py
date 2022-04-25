"""Exports to template file
"""

from gremlin.common import InputType
import gremlin.error
import logging

ignore_pattern = ["[", ";"]
ignore_binding = ["#"]
vjoy_map = {} # todo: fill this with clod device name to vjoy_id mapping

axis_id_to_string = {
    1: "X",
    2: "Y",
    3: "Z",
    4: "RX",
    5: "RY",
    6: "RZ",
    7: "U",
    8: "V",
}

def export(bound_vjoy_list,template_file):
    
    fid = open(template_file, 'r')
    file = fid.readlines()
    for line in file:
        
        # skip empty or comment lines
        # todo: fix this to keep line as-is
        line = line.strip()
        if not line or line[0] in ignore_pattern:
            continue
        
        # get binding and assignment
        binding = line.split("=")[-1].strip()
        assignment = line.split("=")[0].strip()
        
        if binding in bound_vjoy_list.keys():
            bound_item = bound_vjoy_list[binding]
            line = vjoy_item2clod_item(bound_item)
            bound_vjoy_list.pop(binding)
        elif assignment.split("+")[0] in vjoy_map.values():
            # remove old assignment from output data
            line = "; =%s".format(binding)
        
        # todo: write lines to file
    
    for bound_item in bound_vjoy_list.values():
        line = vjoy_item2clod_item(bound_item)
        # todo: write lines to file
        
def vjoy_item2clod_item(bound_item):
    """Return vjoy to string for clod
    
    :param bound_item BoundVJoy instance to write
    """
    # get correct device ID as recognized by CLoD
    try:
            device_str = vjoy_map[bound_item.vjoy_id]
    except KeyError:
        msg = ("IL-2 CLoD device ID not defined for vJoy Device %d!"
               "\nReplace VJoy Description with value in CLoD-generated \"confuser.ini\" config file."
              ).format(bound_item.vjoy_id)
        raise gremlin.error.ExporterError(msg)
    
    # get correct axis/button naming for clod
    input_type = bound_item.input_type
    if input_type == InputType.JoystickAxis:
        input_str = axis_id_to_string(bound_item.input_id)
    elif input_type == InputType.JoystickButton:
        input_str = "Key%d".format(bound_item.input_id - 1)
    else:
        msg = "IL-2 CLoD export not defined for outputs of type \"%s\"".format(InputType.to_string(input_type))
        raise gremlin.error.ExporterError(msg)
    
    return  "%s+%s=%s".format(device_str,input_str,bound_item.binding)
