# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import copy
import logging
import threading
import time
from typing import List, Optional
from xml.etree import ElementTree

from PySide6 import QtCore
from PySide6.QtCore import Property, Signal, Slot

from gremlin import error, util, plugin_manager, profile_library
from gremlin.base_classes import AbstractActionModel, AbstractFunctor
from gremlin.tree import TreeNode
from gremlin.types import InputType, PropertyType
from gremlin.ui.profile import ActionNodeModel


# class TempoContainerWidget(gremlin.ui.input_item.AbstractContainerWidget):

#     """Container with two actions, triggered based on activation duration."""

#     def __init__(self, profile_data, parent=None):
#         """Creates a new instance.

#         :param profile_data the profile data represented by this widget
#         :param parent the parent of this widget
#         """
#         super().__init__(profile_data, parent)

#     def _create_action_ui(self):
#         """Creates the UI components."""
#         self.profile_data.create_or_delete_virtual_button()

#         self.options_layout = QtWidgets.QHBoxLayout()

#         # Activation delay
#         self.options_layout.addWidget(
#             QtWidgets.QLabel("<b>Long press delay: </b>")
#         )
#         self.delay_input = gremlin.ui.common.DynamicDoubleSpinBox()
#         self.delay_input.setRange(0.1, 2.0)
#         self.delay_input.setSingleStep(0.1)
#         self.delay_input.setValue(0.5)
#         self.delay_input.setValue(self.profile_data.delay)
#         self.delay_input.valueChanged.connect(self._delay_changed_cb)
#         self.options_layout.addWidget(self.delay_input)
#         self.options_layout.addStretch()

#         # Activation moment
#         self.options_layout.addWidget(QtWidgets.QLabel("<b>Activate on: </b>"))
#         self.activate_press = QtWidgets.QRadioButton("on press")
#         self.activate_release = QtWidgets.QRadioButton("on release")
#         if self.profile_data.activate_on == "press":
#             self.activate_press.setChecked(True)
#         else:
#             self.activate_release.setChecked(True)
#         self.activate_press.toggled.connect(self._activation_changed_cb)
#         self.activate_release.toggled.connect(self._activation_changed_cb)
#         self.options_layout.addWidget(self.activate_press)
#         self.options_layout.addWidget(self.activate_release)

#         self.action_layout.addLayout(self.options_layout)

#         if self.profile_data.action_sets[0] is None:
#             self._add_action_selector(
#                 lambda x: self._add_action(0, x),
#                 "Short Press"
#             )
#         else:
#             self._create_action_widget(
#                 0,
#                 "Short Press",
#                 self.action_layout,
#                 gremlin.ui.common.ContainerViewTypes.Action
#             )

#         if self.profile_data.action_sets[1] is None:
#             self._add_action_selector(
#                 lambda x: self._add_action(1, x),
#                 "Long Press"
#             )
#         else:
#             self._create_action_widget(
#                 1,
#                 "Long Press",
#                 self.action_layout,
#                 gremlin.ui.common.ContainerViewTypes.Action
#             )

#     def _create_condition_ui(self):
#         if self.profile_data.activation_condition_type == "action":
#             if self.profile_data.action_sets[0] is not None:
#                 self._create_action_widget(
#                     0,
#                     "Short Press",
#                     self.activation_condition_layout,
#                     gremlin.ui.common.ContainerViewTypes.Condition
#                 )

#             if self.profile_data.action_sets[1] is not None:
#                 self._create_action_widget(
#                     1,
#                     "Long Press",
#                     self.activation_condition_layout,
#                     gremlin.ui.common.ContainerViewTypes.Condition
#                 )

#     def _add_action_selector(self, add_action_cb, label):
#         """Adds an action selection UI widget.

#         :param add_action_cb function to call when an action is added
#         :param label the description of the action selector
#         """
#         action_selector = gremlin.ui.common.ActionSelector(
#             self.profile_data.get_input_type()
#         )
#         action_selector.action_added.connect(add_action_cb)

#         group_layout = QtWidgets.QVBoxLayout()
#         group_layout.addWidget(action_selector)
#         group_layout.addStretch(1)
#         group_box = QtWidgets.QGroupBox(label)
#         group_box.setLayout(group_layout)

#         self.action_layout.addWidget(group_box)

#     def _create_action_widget(self, index, label, layout, view_type):
#         """Creates a new action widget.

#         :param index the index at which to store the created action
#         :param label the name of the action to create
#         """
#         widget = self._create_action_set_widget(
#             self.profile_data.action_sets[index],
#             label,
#             view_type
#         )
#         layout.addWidget(widget)
#         widget.redraw()
#         widget.model.data_changed.connect(self.container_modified.emit)

#     def _add_action(self, index, action_name):
#         """Adds a new action to the container.

#         :param action_name the name of the action to add
#         """
#         plugin_manager = gremlin.plugin_manager.ActionPlugins()
#         action_item = plugin_manager.get_class(action_name)(self.profile_data)
#         if self.profile_data.action_sets[index] is None:
#             self.profile_data.action_sets[index] = []
#         self.profile_data.action_sets[index].append(action_item)
#         self.profile_data.create_or_delete_virtual_button()
#         self.container_modified.emit()

#     def _delay_changed_cb(self, value):
#         """Updates the activation delay value.

#         :param value the value after which the long press action activates
#         """
#         self.profile_data.delay = value

#     def _activation_changed_cb(self, value):
#         """Updates the activation condition state.

#         :param value whether or not the selection was toggled - ignored
#         """
#         if self.activate_press.isChecked():
#             self.profile_data.activate_on = "press"
#         else:
#             self.profile_data.activate_on = "release"

#     def _handle_interaction(self, widget, action):
#         """Handles interaction icons being pressed on the individual actions.

#         :param widget the action widget on which an action was invoked
#         :param action the type of action being invoked
#         """
#         index = self._get_widget_index(widget)
#         if index != -1:
#             if index == 0 and self.profile_data.action_sets[0] is None:
#                 index = 1
#             self.profile_data.action_sets[index] = None
#             self.container_modified.emit()

#     def _get_window_title(self):
#         """Returns the title to use for this container.

#         :return title to use for the container
#         """
#         if self.profile_data.is_valid():
#             return "Tempo: ({}) / ({})".format(
#                 ", ".join([a.name for a in self.profile_data.action_sets[0]]),
#                 ", ".join([a.name for a in self.profile_data.action_sets[1]])
#             )
#         else:
#             return "Tempo"


class TempoContainerFunctor(AbstractFunctor):

    def __init__(self, action):
        super().__init__(action)

        self.start_time = 0
        self.timer = None
        self.value_press = None
        self.event_press = None

    def process_event(self, event, value):
        # TODO: Currently this does not handle hat or axis events, however
        #       virtual buttons created on those inputs is supported
        if not isinstance(value.current, bool):
            logging.getLogger("system").warning(
                "Invalid data type received in Tempo container: {}".format(
                    type(event.value)
                )
            )
            return False

        # Copy state when input is pressed
        if value.current:
            self.value_press = copy.deepcopy(value)
            self.event_press = event.clone()

        # Execute tempo logic
        if value.current:
            self.start_time = time.time()
            self.timer = threading.Timer(self.delay, self._long_press)
            self.timer.start()

            if self.activate_on == "press":
                self.short_set.process_event(self.event_press, self.value_press)
        else:
            # Short press
            if (self.start_time + self.delay) > time.time():
                self.timer.cancel()

                if self.activate_on == "release":
                    threading.Thread(target=lambda: self._short_press(
                        self.event_press,
                        self.value_press,
                        event,
                        value
                    )).start()
                else:
                    self.short_set.process_event(event, value)
            # Long press
            else:
                self.long_set.process_event(event, value)
                if self.activate_on == "press":
                    self.short_set.process_event(event, value)

            self.timer = None

        return True

    def _short_press(self, event_p, value_p, event_r, value_r):
        """Callback executed for a short press action.

        :param event_p event to press the action
        :param value_p value to press the action
        :param event_r event to release the action
        :param value_r value to release the action
        """
        self.short_set.process_event(event_p, value_p)
        time.sleep(0.05)
        self.short_set.process_event(event_r, value_r)

    def _long_press(self):
        """Callback executed, when the delay expires."""
        self.long_set.process_event(self.event_press, self.value_press)


class TempoModel(AbstractActionModel):

    """A container with two actions which are triggered based on the duration
    of the activation.

    A short press will run the fist action while a longer press will run the
    second action.
    """

    version = 1
    name = "Tempo"
    tag = "tempo"

    functor = TempoContainerFunctor
    
    input_types = [
        InputType.JoystickAxis,
        InputType.JoystickButton,
        InputType.JoystickHat,
        InputType.Keyboard
    ]

    actionsChanged = Signal()
    activateOnChanged = Signal()
    thresholdChanged = Signal()

    def __init__(
            self,
            action_tree: profile_library.ActionTree,
            input_type: InputType = InputType.JoystickButton,
            parent: Optional[QtCore.QObject] = None
    ):
        """Creates a new instance.

        :param parent the InputItem this container is linked to
        """
        super().__init__(action_tree, input_type, parent)
        self._short_action_ids = []
        self._long_action_ids = []
        self._threshold = 0.5
        self._activate_on = "release"

    def from_xml(self, node: ElementTree.Element) -> None:
        self._id = util.read_action_id(node)
        self._short_action_ids = util.read_action_ids(node.find("short-actions"))
        self._long_action_ids = util.read_action_ids(node.find("long-actions"))
        self._threshold = util.read_property(
            node, "threshold", PropertyType.Float
        )
        self._activate_on = util.read_property(
            node, "activate-on", PropertyType.String
        )
        if self._activate_on not in ["press", "release"]:
            raise error.ProfileError(f"Invalid activat-on value present: {self._activate_on}")

    def to_xml(self) -> ElementTree.Element:
        """Returns an XML node representing this container's data.

        :return XML node representing the data of this container
        """
        node = util.create_action_node(TempoModel.tag, self._id)
        node.append(util.create_action_ids(
            "short-actions", self._short_action_ids
        ))
        node.append(util.create_action_ids(
            "long-actions", self._long_action_ids
        ))
        node.append(util.create_property_node(
            "threshold", self._threshold, PropertyType.Float
        ))
        node.append(util.create_property_node(
            "activate-on", self._activate_on, PropertyType.String
        ))

        return node
    
    def qml_path(self) -> str:
        return "file:///" + QtCore.QFile(
            "core_plugins:tempo/TempoAction.qml"
        ).fileName()

    def is_valid(self) -> True:
        return True

    @Slot(str, str)
    def addAction(self, action_name: str, activation: str) -> None:
        """Adds a new action to one of the two condition branches.

        Args:
            action_name: name of the action to add
            activation: which of the two activation types to add the action two, valid
                options are [short, long]
        """
        action = plugin_manager.ActionPlugins().get_class(action_name)(
            self._action_tree,
            self._input_type
        )

        predicate = lambda x: True if x.value and x.value.id == self.id else False
        nodes = self._action_tree.root.nodes_matching(predicate)
        if len(nodes) != 1:
            raise error.GremlinError(f"Node with ID {self.id} has invalid state")
        nodes[0].add_child(TreeNode(action))
        if activation == "short":
            self._short_action_ids.append(action.id)
        elif activation == "long":
            self._long_action_ids.append(action.id)
        else:
            raise error.GremlinError(f"Invalid branch specification: {activation}")

        self.actionsChanged.emit()

    @Property(list, notify=actionsChanged)
    def shortActions(self) -> List[ActionNodeModel]:
        return self._create_node_list(self._short_action_ids)

    @Property(list, notify=actionsChanged)
    def longActions(self) -> List[ActionNodeModel]:
        return self._create_node_list(self._long_action_ids)

    def _set_threshold(self, value: float) -> None:
        if self._threshold != value:
            self._threshold = value
            self.thresholdChanged.emit()

    @Property(float, fset=_set_threshold, notify=thresholdChanged)
    def threshold(self) -> float:
        return self._threshold
    
    def _set_activate_on(self, value: str) -> None:
        if value not in ["press", "release"]:
            raise error.GremlinError(f"Received invalid activateOn value {value}")

        if self._activate_on != value:
            self._activate_on = value
            self.activateOnChanged.emit()
    
    @Property(str, fset=_set_activate_on, notify=activateOnChanged)
    def activateOn(self) -> str:
        return self._activate_on
                

create = TempoModel