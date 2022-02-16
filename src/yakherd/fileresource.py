
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

from yakherd import container
from yakherd import filesystem
import configparser
import json

# ConfigurationDict {{{1

class ConfigurationDict(container.AttributeSetterDict):

    """
    -   Handles parsing data from a variety of formats, mapping them into a *flat*
        dictionary.
        -   regardless of data format, expects the data value to be a single
            dictionary of key-value pairs (with string keys and values that
            include various types such as primitives as well as both simple as
            well as nested lists or dictionaries)
        -   nested dictionaries will be "flattened": keys will be created
            corresponding to a dot-separated path such that:
                { "d1": {
                    "da": 1,
                    },
                }
            will become:
                {"d1.da": 1}
    """

    # init {{{2
    def __init__(self):
        super().__init__(self)
        self.dict_path_separator = "."
        self._raw_d = {}
    # }}}2 init

    # reading/parsing {{{2
    def read(self, path, file_type, **kwargs):
        path = filesystem.expand_path(path)
        if file_type == "json":
            d = self._read_json(path, **kwargs)
        elif file_type == "ini":
            d = self._read_ini(path, **kwargs)
        else:
            raise ValueError(file_type)
        return self

    def _read_json(self, path, **kwargs):
        with open(path) as src:
            try:
                d = json.load(src)
                self._raw_d.update(d)
                self.update(container.flatten_dict(d, separator=self.dict_path_separator))
            except json.decoder.JSONDecodeError as e:
                raise
                # raise error.SourceFormatError.from_json(e, src.name) from e

    def _read_ini(self, path, **kwargs):
        config = configparser.ConfigParser(**kwargs)
        config.read(path)
        for section in config.sections():
            self._raw_d[section] = {}
            for option, value in config.items(section):
                self._raw_d[section][option] = value
                flat_key = self.dict_path_separator.join([section, option])
                self[ flat_key ] = value
    # }}}2 reading/parsing

    # sugar {{{2

    def get(self, *args, default=None):
        return super().get( self.dict_path_separator.join(args), default)

    def __getitem__(self, *args):
        return super().__getitem__(self.dict_path_separator.join(args) )

    def check(self, *args):
        try:
            return self.__getitem__(*args)
        except KeyError:
            return None

    # }}}2 sugar

# }}}1 ConfigurationDict
