# Style Guide

We follow the [PEP 8](https://peps.python.org/pep-0008/) style guide, everything else in here should be considered additional rules to follow.

All code is to use type hints, where we statically check types during the CI/CD process to not slow down performance. The only exception to this is when we use functions/ABIs we expect developers to use, where they should/need to use correct types in order for the functions to work correctly. 

## Classes

Classes should follow the following ordering:

```python
class MyClass:
    # Class Attributes
    # ------------------------------------------------------------------------
    class_attribute = "I'm a class attribute"

    # Initialization
    # ------------------------------------------------------------------------
    def __init__(self):
        self.instance_attribute = "I'm an instance attribute"

    # Special Methods
    # ------------------------------------------------------------------------
    def __str__(self):
        return f"MyClass instance: {self.instance_attribute}"

    def __repr__(self):
        return f"MyClass({self.instance_attribute!r})"

    # Public Methods
    # ------------------------------------------------------------------------
    def public_method(self):
        return "I'm a public method"

    # Internal Methods
    # ------------------------------------------------------------------------
    def _internal_method(self):
        return "I'm an internal method"

    # Properties
    # ------------------------------------------------------------------------
    @property
    def my_property(self):
        return "I'm a property"

    # Class Methods
    # ------------------------------------------------------------------------
    @classmethod
    def class_method(cls):
        return "I'm a class method"

    # Static Methods
    # ------------------------------------------------------------------------
    @staticmethod
    def static_method():
        return "I'm a static method"
```
