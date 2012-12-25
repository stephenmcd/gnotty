
from collections import namedtuple


Event = namedtuple("Event", ["name", "args"])


def on(event, *args, **kwargs):
    """
    Event method wrapper for bot mixins. When a bot is constructed,
    its metaclass inspects all members of all base classes, and
    looks for methods marked with an event attribute which is assigned
    via this wrapper. It then stores all the methods in a dict
    that maps event names to lists of these methods, which are each
    called when the event occurs.
    """
    def wrapper(func):
        for i, arg in args:
            kwargs[i] = arg
        func.event = Event(event, kwargs)
        return func
    return wrapper
