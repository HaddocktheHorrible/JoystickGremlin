"""Exports to template file
"""

from gremlin.common import InputType
import gremlin.error
import logging

ignore_pattern = ["[", ";"]
ignore_binding = ["#"]
vjoy_map = {
    1: "vJoy_Device-66210FF9",
    2: "vJoy_Device-A4E92C9",
    3: "vJoy_Device-BBF5032F"
    } # todo: replace with profile-based lookup

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
    oldfile = fid.readlines()
    newfile = []
    
    # overwrite old bindings in-place
    for line in oldfile:
        line = line.strip()
        if line and line[0] not in ignore_pattern:
            binding = line.split("=")[-1].strip()
            assignment = line.split("=")[0].strip()
            if binding in bound_vjoy_list.keys():
                bound_item = bound_vjoy_list[binding]
                line = vjoy_item2clod_item(bound_item)
                bound_vjoy_list.pop(binding)
            elif assignment.split("+")[0] in vjoy_map.values():
                # remove old assignment from output data
                line = "; =%s".format(binding)
        newfile.append(line)
    
    # append unsorted bindings to file
    newfile.append(["[Unsorted Gremlin Bindings]\n"])
    for bound_item in bound_vjoy_list.values():
        newfile.append(vjoy_item2clod_item(bound_item))
        
    return newfile
        
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
