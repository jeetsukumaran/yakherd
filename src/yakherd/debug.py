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

import logging
import copy
import textwrap
import re
import os
import sys
import inspect
from yakherd import textprocessing

def stack_trace(
    fields=None,
    message=None,
    out=None,
    start_idx=1,
    end_idx=None,
):
    if fields is None:
        fields = (
            "function",
            "classname",
            "filename",
            "lineno",
        )
    rows = []
    for idx, frame in enumerate(inspect.stack()[start_idx:end_idx]):
        d = {}
        # d["method"] = frame[0].f_code.co_name
        try:
            d["classname"] = frame[0].f_locals["self"].__class__.__name__
        except KeyError:
            d["classname"] = ""
        row = {}
        for field in fields:
            try:
                row[field] = d[field]
            except KeyError:
                row[field] = getattr(frame, field)
        rows.append(row)
    t = textprocessing.format_dict_table(rows)
    if out is None:
        out = sys.stderr
    if message is not None:
         out.write("{}\n".format(message))
    out.write(t)
    out.write("\n")
    out.flush()


