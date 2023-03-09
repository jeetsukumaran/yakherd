#! /usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
## Copyright (c) 2021 Jeet Sukumaran.
## All rights reserved.
##
## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are met:
##
##     * Redistributions of source code must retain the above copyright
##       notice, this list of conditions and the following disclaimer.
##     * Redistributions in binary form must reproduce the above copyright
##       notice, this list of conditions and the following disclaimer in the
##       documentation and/or other materials provided with the distribution.
##     * The names of its contributors may not be used to endorse or promote
##       products derived from this software without specific prior written
##       permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
## ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
## DISCLAIMED. IN NO EVENT SHALL JEET SUKUMARAN BE LIABLE FOR ANY DIRECT,
## INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
## BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
## LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
## OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##
##############################################################################

import heapq
import collections


def flatten_dict(d, separator=".", parent_key=""):
    items = []
    for k, v in d.items():
        new_key = str(parent_key) + separator + str(k) if parent_key else str(k)
        if v and isinstance(v, collections.MutableMapping):
            items.extend(
                flatten_dict(v, separator=separator, parent_key=parent_key).items()
            )
        else:
            items.append((new_key, v))
    return dict(items)


class ObjectHeap:
    """
    Object-oriented wrapper of `heapq`, with no requirement that heap items
    define a bound `__lt__` method. Instead, ``key_fn`` will be used: this
    should be a function that takes two arguments, and returns the `__lt__`
    ranking value.
    """

    class _ObjectHeapItem:
        def __init__(
            self,
            containing_heap,
            value,
        ):
            self._containing_heap = containing_heap
            self._value = value

        def __lt__(self, other):
            # return self._containing_heap.key_fn(self._value) < self._containing_heap.key_fn(other._value)
            return self._containing_heap.key_fn(self._value, other._value)

    def __init__(self, initial=None, key_fn=lambda x: x):
        self.key_fn = key_fn
        self.index = 0
        self._item_factory = ObjectHeap._ObjectHeapItem
        if initial:
            self._data = [self._item_factory(self, v) for v in initial]
            heapq.heapify(self._data)
        else:
            self._data = []

    @property
    def key_fn(self):
        if (
            not hasattr(self, "_key_fn")
            or self._key_fn is None
        ):
            self._key_fn = lambda o1, o2: o1 < o2
        return self._key_fn
    @key_fn.setter
    def key_fn(self, value):
        self._key_fn = value
        if hasattr(self, "_data") and self._data:
            heapq.heapify(self._data)
    @key_fn.deleter
    def key_fn(self):
        del self._key_fn

    def push(self, item):
        heapq.heappush(self._data, self._item_factory(self, item))
        self.index += 1

    def pop(self):
        return heapq.heappop(self._data)[2].value


class AttributeSetterDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_attributes(
        self,
        obj,
        key_map_fn=None,
    ):
        if key_map_fn is None:
            key_map_fn = lambda k: k
        for key, value in self.items():
            try:
                attr_name = key_map_fn(key)
            except KeyError:
                attr_name = key
            setattr(obj, attr_name, value)
        return obj

    def as_attributes(self, key_map_fn=None):
        d = lambda: None
        return self.set_attributes(
            obj=d,
            key_map_fn=key_map_fn,
        )


class Table:
    """
    A *table* serves to transact/extract/organize data from the system.
    Data is stored as mapping of (unique) *labels* (`str` or any type that can
    be coerced into a `str`) to values (`str` or any type that can be coerced
    into a `str`) for a particular *field*.

    """

    class Record(dict):
        pass

    def __init__(
        self,
    ):
        self._records = []

    def add(self, record, label=None):
        self._records.append(record)


class AttributeMap(dict):

    """
    A dictionary that supports access using attributes as well as a key.
    """

    def __init__(self, d=None):
        super().__init__(self)
        # self.is_locked_keys = False
        if d is not None:
            for k, v in d.items():
                self[k] = v

    def __getattr__(self, attr_key):
        if attr_key in self:
            return self[attr_key]
        else:
            raise AttributeError("No such attribute: " + attr_key)

    def __setattr__(self, attr_key, value):
        # if attr_key == "is_locked_keys":
        #     super().__setitem__(attr_key, value)
        # elif self.is_locked_keys:
        #     raise TypeError(f"{type(self)} instance key creation disabled")
        self[attr_key] = value

    def __delattr__(self, attr_key):
        # if self.is_locked_keys:
        #     raise TypeError(f"{type(self)} instance key deletion disabled")
        if attr_key in self:
            del self[attr_key]
        else:
            raise AttributeError("No such attribute: " + attr_key)


class RecursiveAttributeMap(AttributeMap):
    def __setitem__(self, attr_key, value):
        if type(value) is dict:
            value = self.__class__(value)
        super().__setitem__(attr_key, value)


class NormalizedAttributeMap(AttributeMap):
    def normalize_key(self, key):
        try:
            return key.replace("-", "_").lower()
        except AttributeError:
            return self.normalize_key(str(key))

    def __getitem__(self, key):
        return AttributeMap.__getitem__(self, self.normalize_key(key))

    def __setitem__(self, key, value):
        return AttributeMap.__setitem__(self, self.normalize_key(key), value)


class RecursiveNormalizedAttributeMap(RecursiveAttributeMap, NormalizedAttributeMap):
    pass


# class RecursiveNormalizedAttributeMap(RecursiveAttributeMap):
#     def normalize_key(self, key):
#         try:
#             return key.replace("-", "_").lower()
#         except AttributeError:
#             return self.normalize_key(str(key))

#     def __getitem__(self, key):
#         return RecursiveAttributeMap.__getitem__(self, self.normalize_key(key))

#     def __setitem__(self, key, value):
#         return RecursiveAttributeMap.__setitem__(self, self.normalize_key(key), value)


class Catalog:
    """
    Manage a collection of unique values mapped to and tracked using unique
    identity keys, with support for bidirectional dereferencing. There is a
    one-to-one mapping of keys to values, and both values and keys are unique.
    """

    def __init__(
        self,
        identity_key_prefix=None,
        identity_key_fn=None,
        # reference_value_identity_key_setter_fn=None,
    ):
        self.identity_key_prefix = identity_key_prefix
        self._identity_key_fn = identity_key_fn
        self._next_reference_value_index = 0
        self._reference_value_identity_key_map = {}
        self._identity_key_reference_value_map = {}
        # if reference_value_identity_key_setter_fn is None:
        #     self._reference_value_identity_key_setter_fn = self.default_reference_value_identity_key_setter_fn
        # else:
        #     self._reference_value_identity_key_setter_fn = reference_value_identity_key_setter_fn

    def add(self, reference_value, identity_key=None):
        assert reference_value not in self._reference_value_identity_key_map
        if identity_key is None:
            identity_key = self.generate_next_identity_key()
            assert identity_key not in self._identity_key_reference_value_map
        assert identity_key is not None
        # if self._reference_value_identity_key_setter_fn:
        #     self._reference_value_identity_key_setter_fn(reference_value, identity_key)
        self._identity_key_reference_value_map[identity_key] = reference_value
        self._reference_value_identity_key_map[reference_value] = identity_key
        self._next_reference_value_index += 1
        return identity_key

    def __setitem__(self, reference_value):
        return self.add(reference_value)

    def delete(self, identity_key):
        reference_value = self._identity_key_reference_value_map[identity_key]
        del self._identity_key_reference_value_map[identity_key]
        del self._reference_value_identity_key_map[reference_value]

    def remove(self, reference_value):
        identity_key = self._reference_value_identity_key_map[reference_value]
        self.delete(identity_key)

    def __len__(self):
        return len(self._reference_value_identity_key_map)

    def __iter__(self):
        return iter(self._reference_value_identity_key_map)

    @property
    def identity_key_fn(self):
        if not hasattr(self, "_identity_key_fn") or self._identity_key_fn is None:
            self._identity_key_fn = self.default_identity_key_fn
        return self._identity_key_fn

    @identity_key_fn.setter
    def identity_key_fn(self, value):
        self._identity_key_fn = value

    @identity_key_fn.deleter
    def identity_key_fn(self):
        del self._identity_key_fn

    def default_identity_key_fn(self, new_reference_value_index):
        return f"{self.identity_key_prefix}{new_reference_value_index:02d}"

    # def default_reference_value_identity_key_setter_fn(self, reference_value, identity_key):
    #     reference_value.identity_key = identity_key

    def generate_next_identity_key(self):
        return self.identity_key_fn(
            new_reference_value_index=self._next_reference_value_index
        )

    def reference_values(self):
        return self._identity_key_reference_value_map.values()

    def identity_key(self, reference_value):
        return self._reference_value_identity_key_map[reference_value]

    def reference_value(self, identity_key):
        return self._identity_key_reference_value_map[identity_key]


class OrderedSet(collections.abc.MutableSet):
    """
    Like 'set', but support for: (repeatable) random choice.

    Maintains order of components, so that random choice etc. will be repeatable
    under the same random seed.

    Based on: https://code.activestate.com/recipes/576694-orderedset/
              Raymond Hettinger on Thu, 19 Mar 2009 (MIT)
    """

    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]  # sentinel node for doubly linked list
        self._data = {}  # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def add(self, key):
        if key not in self._data:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self._data[key] = [key, curr, end]

    def discard(self, key):
        if key in self._data:
            key, prev, next = self._data.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError("set is empty")
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return "%s()" % (self.__class__.__name__,)
        return "%s(%r)" % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)

    def choose(self, rng):
        return rng.choice(list(self._data.keys()))
        # selected_idx = rng.randint(2, len(self._data)-1)
        # for idx, key in enumerate(self._data):
        #     if idx == selected_idx:
        #         return key
