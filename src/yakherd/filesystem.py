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

import os
import sys
import pathlib

# Functions {{{1
def expand_path(path):
    if not path:
        return path
    path = pathlib.Path(os.path.expandvars(path))
    path = path.expanduser()
    return path
# }}}1 Functions

# file_handle {{{1
class file_handle:
    """
    Return file handle for specified path, dealing with various special
    specifications (such as '-' for standard output/input, '/dev/null' etc.).
    On exit, will only close the file handle if it is not standard input,
    output, or error.

    This can be used as a seamless drop-in replacement for open:

        with file_handle("output.txt", "w") as dest:
            dest.write(...)

    Except that it "understands" specifiers such as "-" for standard output/input,
    "/dev/null", etc. can default to these (or other paths as specified) if not path
    is given, and provides some convenience sugar to compose filepaths
    with augmentation of prefixes and suffixes.

    It can also allows you to (for whatever reason) generate multiple handles that
    write to standard output/error (or read from standard input) without worrying
    about one closing the other.

    For e.g,:

        if is_write_log_to_stdout:
            log_f = sys.stdout
        else:
            log_f = open(...)
        if is_write_data_to_stdout:
            data_f = sys.stdout
        else:
            data_f = open(...)
        with log_f:
            log_f.write(...)
            .
            .
            .
            with data_f:
                for src in srcs:
                    data_f.write(...)
            # if both log_f and data_f are writing to standard output
            # then 'log_f' will have it's handle closed by exiting data_f's
            # context.
            log_f.write(...)

    vs:

        with file_handle(..., "w") as log_f:
            log_f.write(...)
            with file_handle(..., "w") as data_f:
                for src in srcs:
                    data_f.write(...)
            # still open
            log_f.write(...)

    All *args and **kwargs passed to underlying 'open'.

    """

    def __init__(
        self,
        path: str,
        mode: str = "r",
        prefix=None,
        suffix=None,
        default_path=None,
        existing_file=None,
        is_allow_standard_streams=True,
        *args,
        **kwargs
    ):
        if path is None:
            path = default_path
        if path is None or path == "/dev/null":
            self._filepath = os.devnull
        elif path != "-":
            self._filepath = "{}{}{}".format(
                prefix if prefix is not None else "",
                path,
                suffix if suffix is not None else "",
            )
            self._filepath = os.path.expanduser(os.path.expandvars(self._filepath))
        else:
            self._filepath = "-"
        if self._filepath == "-":
            if not is_allow_standard_streams:
                raise ValueError(
                    "Standard input/output/error not supported for this file"
                )
            if "r" in mode:
                stream = sys.stdin
            else:
                stream = sys.stdout
            if "b" in mode:
                fh = stream.buffer  # type: IO
            else:
                fh = stream
        else:
            if (
                existing_file
                and existing_file != "overwrite"
                and self._filepath != os.devnull
            ):
                if os.path.exists(self._filepath):
                    if existing_file == "raise":
                        raise FileExistsError(self._filepath)
                    elif existing_file.startswith("exit"):
                        try:
                            # can specify custom exist message by:
                            # existing_file="exit:File '{}' already exists; use '-y' to overwrite."
                            message = existing_file.split(":")[1].strip()
                        except IndexError:
                            message = "Output file already exists: '{}'"
                        sys.exit(message.format(self._filepath))
            fh = open(self._filepath, mode, *args, **kwargs)
        self._fh = fh

    def __enter__(self):
        return self._fh

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if not self._fh.closed and self._fh not in (sys.stdin, sys.stdout, sys.stderr):
            try:
                self._fh.close()
            except AttributeError:
                pass

    def __getattr__(self, attr):
        """
        Pass through all other calls to underlying file handle.

        (Note to future self: `__getattr__` gets called after all other lookups fail.
        `__getattribute__` gets called before looking at object attributes.
        __getattribute__ will be called for every access, and __getattr__ will
        be called for the times that __getattribute__ raised an AttributeError)
        """
        return object.__getattribute__(self._fh, attr)

    @property
    def name(self):
        return self._filepath

    # @name.setter
    # def name(self, value):
    #     self._filepath = value
    # @name.deleter
    # def name(self):
    #     del self._filepath


# }}}1 file_handle

