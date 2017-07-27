# Load and dump a CAN database in KCD format.
import logging

from xml.etree.ElementTree import fromstring

from ..signal import Signal
from ..message import Message
from ..node import Node
from ..database import Database

from .utils import num


LOGGER = logging.getLogger(__name__)

# The KCD XML namespace.
NAMESPACE = 'http://kayak.2codeornot2code.org/1.0'
NAMESPACES = {'ns': NAMESPACE}


def _load_signal_element(signal):
    """Load given signal element and return a signal object.

    """

    # Default values.
    name = None
    offset = None
    length = 1
    byte_order = 'big_endian'
    is_signed = False
    minimum = None
    maximum = None
    slope = 1
    intercept = 0
    unit = None
    notes = None

    # Signal XML attributes.
    for key, value in signal.attrib.items():
        if key == 'name':
            name = value
        elif key == 'offset':
            offset = int(value)
        elif key == 'length':
            length = int(signal.attrib['length'])
        elif key == 'endianess':
            byte_order = '{}_endian'.format(signal.attrib['endianess'])
        else:
            LOGGER.debug("Ignoring unsupported signal attribute '%s'.", key)

    # Value XML element.
    value = signal.find('ns:Value', NAMESPACES)

    if value is not None:
        for key, value in value.attrib.items():
            if key == 'min':
                minimum = num(value)
            elif key == 'max':
                maximum = num(value)
            elif key == 'slope':
                slope = num(value)
            elif key == 'intercept':
                intercept = num(value)
            elif key == 'unit':
                unit = value
            elif key == 'type':
                is_signed = (value == 'signed')
            else:
                LOGGER.debug("Ignoring unsupported signal value attribute '%s'.",
                             key)

    # Notes.
    try:
        notes = signal.find('ns:Notes', NAMESPACES).text
    except AttributeError:
        pass

    return Signal(name=name,
                  start=offset,
                  length=length,
                  nodes=[],
                  byte_order=byte_order,
                  is_signed=is_signed,
                  scale=slope,
                  offset=intercept,
                  minimum=minimum,
                  maximum=maximum,
                  unit=unit,
                  choices=None,
                  comment=notes,
                  is_multiplexer=False,
                  multiplexer_id=None)


def _load_message_element(message):
    """Load given message element and return a message object.

    """

    # Default values.
    name = None
    frame_id = None
    is_extended_frame = False
    notes = None

    # Message XML attributes.
    for key, value in message.attrib.items():
        if key == 'name':
            name = value
        elif key == 'id':
            frame_id = int(value, 0)
        elif key == 'format':
            is_extended_frame = (value == 'extended')
        else:
            LOGGER.debug("Ignoring unsupported message attribute '%s'.", key)

    # Comment.
    try:
        notes = message.find('ns:Notes', NAMESPACES).text
    except AttributeError:
        pass

    # Find all signals in this message.
    signals = []

    for signal in message.findall('ns:Signal', NAMESPACES):
        signals.append(_load_signal_element(signal))

    return Message(frame_id=frame_id,
                   is_extended_frame=is_extended_frame,
                   name=name,
                   length=8,
                   nodes=[],
                   send_type=None,
                   cycle_time=None,
                   signals=signals,
                   comment=notes)


def dump_string(database):
    """Format given database in KCD file format.

    """

    return str(database)


def load_string(string):
    """Parse given KCD format string.

    """

    root = fromstring(string)
    nodes = [node.attrib for node in root.findall('./ns:Node', NAMESPACES)]
    messages = []

    for message in root.findall('./ns:Bus/ns:Message', NAMESPACES):
        messages.append(_load_message_element(message))

    return Database(messages,
                    [Node(name=node['name'], comment=None) for node in nodes],
                    [],
                    [],
                    None)
