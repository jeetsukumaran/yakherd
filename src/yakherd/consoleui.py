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

import typing
import argparse
import pathlib
import os
from yakherd import classlib
from yakherd import filesystem

# Globals {{{1
default_key_value_assignment_token = ":="
# }}}1 Globals

# ConsoleStyle {{{1

# Adapted from `click`:
#
#   Copyright 2014 Pallets
#
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions are
#   met:
#
#   1.  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#   2.  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#   3.  Neither the name of the copyright holder nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#   PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#   HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
#   TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#   PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#   LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#   NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#   SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
class ConsoleStyle:

    _ansi_theme_colors = {
        "black": 30,
        "red": 31,
        "green": 32,
        "yellow": 33,
        "blue": 34,
        "magenta": 35,
        "cyan": 36,
        "white": 37,
        "reset": 39,
        "bright_black": 90,
        "bright_red": 91,
        "bright_green": 92,
        "bright_yellow": 93,
        "bright_blue": 94,
        "bright_magenta": 95,
        "bright_cyan": 96,
        "bright_white": 97,
    }
    _ansi_reset_all = "\033[0m"

    @classmethod
    def _interpret_color(cls, color, offset=0):
        if isinstance(color, int):
            return f"{38 + offset};5;{color:d}"
        if isinstance(color, (tuple, list)):
            r, g, b = color
            return f"{38 + offset};2;{r:d};{g:d};{b:d}"
        return str(cls._ansi_theme_colors[color] + offset)

    @classmethod
    def _compose_ansi_code(cls,
        fg: typing.Optional[typing.Union[int, typing.Tuple[int, int, int], str]] = None,
        bg: typing.Optional[typing.Union[int, typing.Tuple[int, int, int], str]] = None,
        bold: typing.Optional[bool] = None,
        dim: typing.Optional[bool] = None,
        underline: typing.Optional[bool] = None,
        overline: typing.Optional[bool] = None,
        italic: typing.Optional[bool] = None,
        blink: typing.Optional[bool] = None,
        reverse: typing.Optional[bool] = None,
        strikethrough: typing.Optional[bool] = None,
    ) -> str:
        """
        Returns the ANSI code for the specified color/attributes.

        Supported color names:

        * ``black`` (might be a gray)
        * ``red``
        * ``green``
        * ``yellow`` (might be an orange)
        * ``blue``
        * ``magenta``
        * ``cyan``
        * ``white`` (might be light gray)
        * ``bright_black``
        * ``bright_red``
        * ``bright_green``
        * ``bright_yellow``
        * ``bright_blue``
        * ``bright_magenta``
        * ``bright_cyan``
        * ``bright_white``
        * ``reset`` (reset the color code only)

        If the terminal supports it, color may also be specified as:

        -   An integer in the interval [0, 255]. The terminal must support
            8-bit/256-color mode.
        -   An RGB tuple of three integers in [0, 255]. The terminal must
            support 24-bit/true-color mode.

        See https://en.wikipedia.org/wiki/ANSI_color and
        https://gist.github.com/XVilka/8346728 for more information.

        :param fg: if provided this will become the foreground color.
        :param bg: if provided this will become the background color.
        :param bold: if provided this will enable or disable bold mode.
        :param dim: if provided this will enable or disable dim mode.  This is
                    badly supported.
        :param underline: if provided this will enable or disable underline.
        :param overline: if provided this will enable or disable overline.
        :param italic: if provided this will enable or disable italic.
        :param blink: if provided this will enable or disable blinking.
        :param reverse: if provided this will enable or disable inverse
                        rendering (foreground becomes background and the
                        other way round).
        :param strikethrough: if provided this will enable or disable
            striking through text.
        """
        parts = []
        if fg:
            try:
                parts.append(f"\033[{cls._interpret_color(fg)}m")
            except KeyError:
                raise TypeError(f"Unknown color {fg!r}") from None
        if bg:
            try:
                parts.append(f"\033[{cls._interpret_color(bg, 10)}m")
            except KeyError:
                raise TypeError(f"Unknown color {bg!r}") from None
        if bold is not None:
            parts.append(f"\033[{1 if bold else 22}m")
        if dim is not None:
            parts.append(f"\033[{2 if dim else 22}m")
        if underline is not None:
            parts.append(f"\033[{4 if underline else 24}m")
        if overline is not None:
            parts.append(f"\033[{53 if overline else 55}m")
        if italic is not None:
            parts.append(f"\033[{3 if italic else 23}m")
        if blink is not None:
            parts.append(f"\033[{5 if blink else 25}m")
        if reverse is not None:
            parts.append(f"\033[{7 if reverse else 27}m")
        if strikethrough is not None:
            parts.append(f"\033[{9 if strikethrough else 29}m")
        return "".join(parts)

    def __init__(self, *args, **kwargs):
        self._ansi_code = self._compose_ansi_code(*args, **kwargs)

    def apply(self, text, reset=True, reverse=False):
        if reset:
            reset_code = self._ansi_reset_all
        else:
            reset_code = ""
        if reverse:
            reverse_code = "\033[7m"
            unreverse_code = "\033[27m"
        else:
            reverse_code = ""
            unreverse_code = ""
        s = "{i}{a}{t}{u}{r}".format(
            i=reverse_code,
            a=self.ansi_code,
            t=text,
            u=unreverse_code,
            r=reset_code
        )
        return s

    @property
    def ansi_code(self):
        return self._ansi_code
    @ansi_code.setter
    def ansi_code(self, value):
        self._ansi_code = value

# }}}1 ConsoleStyle

# CommandParser {{{1
class CommandParser:

    @staticmethod
    def get_arg_var_name(*args, **kwargs):
        dest = kwargs.get("dest", None)
        if dest:
            return dest
        for arg in args:
            if not arg.startswith("-"):
                return arg[1:].replace("-", "_")
            elif arg.startswith("--"):
                return arg[2:].replace("-", "_")
        raise ValueError("Unable to predict argument name.")


    def __init__(
        self,
        name,
        command_fn=None,
        parser_fn=None,
        attached_parsers=None,
        **kwargs,
    ):
        parent_command = kwargs.pop("parent_command", None)
        if parser_fn is None:
            parser_fn = argparse.ArgumentParser
            kwargs["prog"] = name
        elif "name" not in kwargs:
            kwargs["name"] = name
        if attached_parsers:
            kwargs["parents"] = attached_parsers
        self.parser = parser_fn(**kwargs)
        self.parser.set_defaults(func=self.default_action)
        try:
            self.parser._optionals.title = "General Options"
        except AttributeError:
            pass
        try:
            self.parser._positionals.title = "Arguments"
        except AttributeError:
            pass
        if command_fn is None:
            command_fn = lambda **kwargs: self.parser.print_help()
        self.command_fn = command_fn
        self.subcommands = []
        self.help_tree_indent_width = 2
        self.is_draw_help_tree_edges = True
        self._global_command_context = {}
        self._argument_groups = {}
        self._logger = None
        if parent_command:
            for k,v in parent_command._global_command_context.items():
                self._global_command_context[k] = v
        else:
            self._global_command_context["argument_postprocessing_callbacks"] = {}

    @property
    def name(self):
        return self.parser.prog

    @classlib.cached_property
    def args_d(self):
        return self.parse()

    @classlib.cached_property
    def known_args_d(self):
        parsed_args, remaining_args = self.parser.parse_known_args()
        return vars(parsed_args), vars(remaining_args)

    @classlib.cached_property
    def _subparser(self):
        return self.parser.add_subparsers(title="Commands")

    @property
    def _argument_postprocessing_callbacks(self):
        return self._global_command_context["argument_postprocessing_callbacks"]

    def add_subcommand(
        self,
        name,
        command_fn=None,
        attached_parsers=None,
        **kwargs,
    ):
        parser_fn = self._subparser.add_parser
        subcommand = CommandParser(
            command_fn=command_fn,
            parser_fn=parser_fn,
            attached_parsers=attached_parsers,
            name=name,
            parent_command=self,
            **kwargs,
        )
        self.subcommands.append(subcommand)
        return subcommand

    def add_argument(self, *args, **kwargs):
        return self.parser.add_argument(*args, **kwargs)

    def add_argument_group(self, *args, **kwargs):
        return self.parser.add_argument_group(*args, **kwargs)

    def default_action(self, **kwargs):
        if self.command_fn is None:
            pass
        else:
            self.command_fn(**kwargs)

    def parse(self):
        raw_d = vars(self.parser.parse_args())
        processed_d = {}
        for arg_name in raw_d:
            arg_value = raw_d[arg_name]
            if arg_name in self._argument_postprocessing_callbacks:
                callback_fn = self._argument_postprocessing_callbacks[arg_name]
                arg_value = callback_fn(arg_value)
                pass
            processed_d[arg_name] = arg_value
        return processed_d

    def validate_no_unknown_arguments(self):
        self.parser.parse_args()

    def compose_command_tree(
        self,
        start_indent=0,
    ):
        entries = []
        leader = " " * (start_indent * self.help_tree_indent_width)
        for sc in self.subcommands:
            full_command_name = sc.parser.prog
            # for k, v in sc.parser.__dict__.items():
            #     print(f"{leader}{k}\t\t\t{str(v)[:70]}")
            # print("")
            # continue
            sc_name = full_command_name.split(" ")[-1]
            entries.append(f"{leader}{sc_name}")
            sc_entries = sc.compose_command_tree(
                start_indent=start_indent+1,
            )
            if sc_entries:
                entries.extend(sc_entries)
            # else:
            #     entries.append(sc.parser.format_usage())
        return entries

    @property
    def logger_configuration_parser(self):
        if (
            not hasattr(self, "_logger_configuration_parser")
            or self._logger_configuration_parser is None
        ):
            self._logger_configuration_parser = LoggerConfigurationParser(name=self.name)
        return self._logger_configuration_parser
    @logger_configuration_parser.setter
    def logger_configuration_parser(self, value):
        self._logger_configuration_parser = value
    @logger_configuration_parser.deleter
    def logger_configuration_parser(self):
        del self._logger_configuration_parser

    def attach_logger_options(self, **kwargs):
        if (
            not hasattr(self, "_logger_configuration_parser")
            or self._logger_configuration_parser is None
            or kwargs
            ):
                self._logger_configuration_parser = LoggerConfigurationParser(name=self.name, **kwargs)
        self.logger_configuration_parser = LoggerConfigurationParser(name=self.name, **kwargs)
        self.logger_configuration_parser.attach(self)
        return self.logger_configuration_parser

    def get_logger(self, args_d=None, **kwargs):
        if self._logger is None:
            if args_d is None:
                args_d = self.args_d
            self._logger = self.logger_configuration_parser.get_logger(args_d=args_d, **kwargs)
        return self._logger

    def add_path_argument(
        self,
        *args,
        **kwargs
    ):
        environ_var = kwargs.pop("environ_var", None)
        group = kwargs.pop("group", None)
        group_name = kwargs.pop("group_name", None)
        if group is not None:
            target = group
        elif group_name is not None:
            try:
                target = self._argument_groups[group_name]
            except KeyError:
                group = self.parser.add_argument_group(group_name)
                self._argument_groups[group_name] = group
                target = group
        else:
            target = self.parser
        if "default" not in kwargs and environ_var:
            kwargs["default"] = os.environ.get(environ_var, None)
        target.add_argument(*args, **kwargs)
        key = self.get_arg_var_name(*args, **kwargs)
        self._argument_postprocessing_callbacks[key] = lambda value: self.process_path_argument(
            value=value,
            environ_var=environ_var,
        )

    def process_path_argument(
        self,
        value=None,
        environ_var=None,
        fallback_value=None,
    ):
        path = value
        if isinstance(path, list) or isinstance(path, tuple):
            return [self.process_path_argument(
                value=i,
                environ_var=environ_var,
                default_path=default_path,
            ) for i in path]
        if not path:
            if environ_var and environ_var in os.environ:
                path = os.environ[environ_var]
            else:
                path = fallback_value
        return filesystem.expand_path(path)

    def resolve_value(
        self,
        command_name=None,
        environ_var=None,
        config_value=None,
        fallback_value=None,
        postprocess_fn=None,
        is_require_value=False,
    ):
        val = None
        if command_name and command_name in self.args_d:
            val = self.args_d[command_name]
        elif environ_var and environ_var in os.environ:
            val = os.environ[environ_var]
        elif config_value:
            val = config_value
        elif fallback_value:
            val = fallback_value
        elif is_require_value:
            raise TypeError("Required value not specified")
        if postprocess_fn:
            val = postprocess_fn(val)
        return val

# }}}1 CommandParser

# AttachableSubParsers {{{1
class AttachableSubParsers:

    @classmethod
    def get_parser(
        cls,
        **kwargs
    ):
        p = cls(**kwargs,)
        return p.attach(**kwargs)

    def attach(
        self,
        command,
        **kwargs,
    ):
        return self.attach_to_parser(
            parser=command.parser,
            **kwargs
        )

# AttachableSubParsers }}}1

# LoggerConfigurationParser {{{1

class LoggerConfigurationParser(AttachableSubParsers):
    """

    Usage With `CommandParser`
    --------------------------

    ::
        import yakherd

        main_cmd = yakherd.CommandParser(name="Foo")
        main_cmd.attach_logger_options()
        logger = main_cmd.get_logger()
        logger.log_info("Hello, world")

    Or::
        import yakherd

        main_cmd = yakherd.CommandParser(
            name="Foo",
            attached_parsers=[
                yakherd.LoggerConfigurationParser.get_parser(),
            ],
        )
        logger = main_cmd.get_logger()
        logger.log_info("Hello, world")


    Usage With `argparse`
    ---------------------

    ::
        import argparse
        import yakherd

        parser = argparse.ArgumentParser()
        logger_configuration_parser = yakherd.LoggerConfigurationParser(name="Foo")
        logger_configuration_parser.attach(parser)
        args = parser.parse_args()
        logger = logger_configuration_parser.get_logger(args_d=vars(args))
        logger.log_info("Hello, world")


    """

    def __init__(
        self,
        name="command",
        default_log_path=None,
    ):
        self.name = name
        self.default_log_path = default_log_path

    def attach_to_parser(
        self,
        parser=None,
        console_logging_group=None,
        file_logging_group=None,
        console_logging_group_name="Console Logging Options",
        file_logging_group_name="File Logging Options",
    ):
        if parser is None:
            parser = argparse.ArgumentParser(add_help=False)
        if console_logging_group is None:
            console_logging_group = parser.add_argument_group(console_logging_group_name)
        elif console_logging_group is False:
            console_logging_group = parser
        if file_logging_group is None:
            file_logging_group = parser.add_argument_group(file_logging_group_name)
        elif file_logging_group is False:
            file_logging_group = parser
        console_logging_group.add_argument(
            "--verbosity",
            metavar="NOISE-LEVEL",
            dest="__logging_max_allowed_message_noise_level",
            type=int,
            default=1,
            help="Maximum allowed message noise level [default = %(default)s].",
        )
        console_logging_group.add_argument(
            "-q",
            "--quiet",
            "--no-console-log",
            action="store_true",
            dest="__logging_no_console_log",
            help="Do not write logs to console.",
        )
        console_logging_group.add_argument(
            "--console-color-theme",
            dest="__logging_color_theme",
            metavar="THEME",
            default="default-dark-bg",
            help="Theme for output colors ('default-dark-bg', 'None')",
        )
        console_logging_group.add_argument(
            "--console-no-color",
            action="store_true",
            dest="__logging_no_color",
            default=None,
            help="Do not write to console in color.",
        )
        file_logging_group = parser.add_argument_group("File Logging Options")
        file_logging_group.add_argument(
            "--logfile",
            metavar="FILE",
            dest="__logging_file_path",
            default=None,
            help="Path to write logs.",
        )
        return parser

    def get_logger(self, args_d, **kwargs):
        from yakherd import Logger
        if not hasattr(args_d, "__get__") and not isinstance(args_d, dict):
            args_d = vars(args_d)
        if args_d.get(
            "__logging_color_theme", "none"
        ).lower() == "none" or args_d.get("__logging_no_color", True):
            is_colorize = False
        else:
            is_colorize = True
        log_fpath = args_d.get("__logging_file_path", self.default_log_path)
        if log_fpath is not None:
            is_enable_log_file = True
            log_fpath = pathlib.Path(log_fpath)
        else:
            is_enable_log_file = False
            log_fpath = None
        logger = Logger(
            name=self.name,
            max_allowed_message_noise_level=args_d.get(
                "__logging_max_allowed_message_noise_level", 0
                ),
            is_enable_console=not args_d.get(
                "__logging_no_console_log", False
                ),
            is_colorize=is_colorize,
            is_enable_log_file=is_enable_log_file,
            logfile_path=log_fpath,
            **kwargs,
            )
        return logger


# }}}1 LoggerConfigurationParser

# PathParser {{{1

class PathParser(AttachableSubParsers):
    def __init__(
        self,
        *args,
        **kwargs
    ):
        self.argument_args = args
        self.argument_kwargs = kwargs

    def attach(self, command):
        command.add_path_argument(
            *self.argument_args,
            **self.argument_kwargs
        )

    def attach_to_parser(self, parser, *args, **kwarg):
        raise ValueError("Cannot be attached directly to parser: require CommandParser target")



# }}}1 PathParser
