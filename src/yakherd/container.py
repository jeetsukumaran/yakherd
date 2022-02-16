
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

import collections

def flatten_dict(d, separator=".", parent_key=""):
    items = []
    for k, v in d.items():
        new_key = str(parent_key) + separator + str(k) if parent_key else str(k)
        if v and isinstance(v, collections.MutableMapping):
            items.extend(flatten_dict(v, separator=separator, parent_key=parent_key).items())
        else:
            items.append((new_key, v))
    return dict(items)


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
