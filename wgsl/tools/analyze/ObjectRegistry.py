#!/usr/bin/env python3
#
# Copyright 2022 Google LLC
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of works must retain the original copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the original
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#
# 3. Neither the name of the W3C nor the names of its contributors
# may be used to endorse or promote products derived from this work
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import json
import functools

class RegistryInfo:
    """
    Info tracked for a registered object
    """
    def __init__(self,registry,obj,index):
        # The ObjectRegistry managing this object
        self.registry = registry
        # The first equivalent registered object
        self.obj = obj
        # The unique integer index for this object, in the context of the registry
        self.index = index

    def __eq__(self,other):
        return (self.index == other.index) and (self.registry == other.registry)


@functools.total_ordering
class RegisterableObject:
    """
    A RegisterableObject can be registered in an ObjectRegistry.

    Required fields:
    .key:
     - objects that should compare as equal have the same key
     - objects that should compare as unequal have a different key
     - keys should be quickly hashable
     - keys must not change

    .class_id:
     - an integer unique to self.__class__

    It has a reg_info object.
    """
    def __init__(self,**kwargs):
        # assert 'key' in dir(self) #. This is surprisingly slow
        self.reg_info = None
        reg = kwargs['reg']
        reg.register(self)

    def register_string(self,string,**kwargs):
        assert isinstance(string,str)
        reg = kwargs['reg']
        return reg.register_string(string)

    def register(self,reg):
        """
        The object must be able to used as a key in a dictionary.
        """
        reg.register(self)

    def __eq__(self,other):
        return self.reg_info == other.reg_info

    def __hash__(self):
        return self.reg_info.index

    def __lt__(self,other):
        return self.reg_info.index < other.reg_info.index


class ObjectRegistry:
    """
    An ObjectRegistry maintains a unique index for unique objects,
    where uniqueness for an object is determined by the pair:
        (object.__class__, object.string_internal())
    """

    def __init__(self):
        # Maps an object key to the object with that key
        self.key_to_object = dict()
        # Maps an object's index to the object
        self.index_to_object = dict()

        # Maps strings to unique integers
        self.str_to_id = dict()

    def register_string(self,string):
        assert isinstance(string,str)
        if string in self.str_to_id:
            return self.str_to_id[string]
        result = len(self.str_to_id)
        self.str_to_id[string] = result
        return result

    def register(self,registerable):
        """
        Registers an indexable object.

        Returns:
            The first object registered that compares as equal.
            If this object is the first such one, then it also
            populates the object's reg_info field.
        """
        if registerable.reg_info is not None:
            # Assume immutability after it's been registered once.
            assert registerable.reg_info.registry is self
            assert registerable.reg_info.obj is not None
            return registerable.reg_info.obj


        key = registerable.key
        if key in self.key_to_object:
            return self.key_to_object[key]

        index = len(self.key_to_object)
        registerable.reg_info = RegistryInfo(self, registerable, index)
        self.key_to_object[key] = registerable
        self.index_to_object[index] = registerable
        return registerable

    def findByIndex(self,index):
        return self.index_to_object[index]

    def __str__(self):
        objects = sorted(self.key_to_object.values(), key = lambda o: o.reg_info.index)
        parts = []
        parts.append("<ObjectRegistry>\n")
        for o in objects:
            parts.append(" {} {}\n".format(o.reg_info.index, str(o)))
        parts.append("</ObjectRegistry>\n")
        return "".join(parts)
