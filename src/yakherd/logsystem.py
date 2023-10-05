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
from yakherd import consoleui
from yakherd import textprocessing

# Logger {{{1


class Logger:

    """
    A logger that establishes two handlers: one to write to the console and one
    to write to a file.

    The console handler will pass through strings with color/markup codes.
    The file handler will strip color/markup codes from strings.

    Parameters
    ----------

    log_format_fmt: str or None
        Specifies the output emitted by the logger. Should include at least "%(msg)s%" if given.
        See `logging.Formatter`_ for details on specificiation. Note that
        handler-specific format specifications (e.g., `console_format_fmt` for console output
        or `logfile_format_fmt` for file output. Conversely, if no handler-specific format
        specifications are given, then this will apply.
    log_format_datefmt: str or None
        As above, but for the `datemft` parameter of the `logging.Formatter`_ class.
    log_format_style: str or None
        As above, but for the `style` parameter of the `logging.Formatter`_ class.

    is_enable_console: bool
    console_format_fmt: str or None
    console_format_datefmt: str or None
    console_format_style: str or None

    is_enable_logfile: bool
    logfile_stream: file or filelike
    logfile_path: str
    logfile_logging_level: logging.Level
    logfile_format_fmt: str or None
    logfile_format_datefmt: str or None
    logfile_format_style: str or None

    debug_message_prefix: str or None
    info_message_prefix: str or None
    warning_message_prefix: str or None
    error_message_prefix: str or None
    critical_message_prefix: str or None

    max_allowed_message_noise_level: int, defaults to 0
        Acts across all channels to filter out messages based on verbosity.

        By default, all messages have a noise level of zero. The default noise
        level threshold for the Logger is also 0. Thus, by default, all
        default-noise level messages will get through on all channels on a
        default `max_allowed_message_noise_level` Logger.

        Messages with positive values require a Logger configured (by, for
        example, user options) to tolerate a higher noise level. So, for example, a message with a noise level of 1 will not be seen in a normal run of the a program, But if the user passes in a `--verbosity 1` option, then pass in this value to the `max_allowed_message_noise_level` argument and the messagge will be seen. As so on with levels 2, 3, etc. This is sometimes also presented as `-v`, `-vv`, `-vvv`, `-vvvv`. In either case note that the default verbosity of 0 is NOT the same as what a `--quiet` flag might do: the former still allows all default noise level messages across all channels, while the latter suppress the console log entirely.

    """

    @staticmethod
    def timestamp():
        import datetime

        timestr = datetime.datetime.now().strftime("%Y%m%d-%H%M%S%f")
        return timestr

    def __init__(self, name="command", **kwargs):
        self.name = name
        self._log = logging.getLogger(self.name)
        self._log.setLevel(logging.DEBUG)
        self.handlers = {}
        self.theme_colors = {
            "metadata": consoleui.ConsoleStyle(fg=116),
            "debug": consoleui.ConsoleStyle(fg=140, bold=True),
            "info": consoleui.ConsoleStyle(fg=None, bold=False),
            "warning": consoleui.ConsoleStyle(fg=208, bold=True),
            "error": consoleui.ConsoleStyle(fg=202, bold=True),
            "critical": consoleui.ConsoleStyle(fg=202, bold=True),
            "banner": consoleui.ConsoleStyle(fg=179, bold=True),
            "heading1": consoleui.ConsoleStyle(fg=131, bold=True),
            "heading2": consoleui.ConsoleStyle(fg=137, bold=True),
            "special": consoleui.ConsoleStyle(fg=109),
            "path": consoleui.ConsoleStyle(fg=138),
            "command": consoleui.ConsoleStyle(fg=107),
            "command_prefix": consoleui.ConsoleStyle(fg=107),
            "data": consoleui.ConsoleStyle(fg=247),
            "process_stdout": consoleui.ConsoleStyle(fg=0, italic=True),
            "process_stderr": consoleui.ConsoleStyle(fg=0, italic=True),
        }
        self.subprocess_command_cwd_reporting_style = "pseudocommand"
        default_message_prefixes = {
            "info": "",
            "debug": self.theme_colors["error"].apply("[DEBUG]", reverse=True),
            "error": self.theme_colors["error"].apply("[ERROR]", reverse=True),
            "warning": self.theme_colors["warning"].apply("[WARNING]", reverse=True),
            "critical": self.theme_colors["critical"].apply("[CRITICAL]", reverse=True),
        }
        for message_type_key in default_message_prefixes:
            message_type_name = "{}_message_prefix".format(message_type_key)
            setattr(
                self,
                message_type_name,
                kwargs.get(
                    message_type_name, default_message_prefixes[message_type_key]
                ),
            )

        # needed to avoid clutter on screen in the case of no handlers
        self._log.addHandler(logging.NullHandler())
        for (handler_prefix_key, default_state, default_stream, formatter_type) in (
            ("console", True, sys.stderr, ConsoleFormatter),
            ("logfile", False, None, LogFileFormatter),
        ):
            if kwargs.get("is_enable_{}".format(handler_prefix_key), default_state):
                formatter = self._create_formatter(
                    formatter_type,
                    kwargs_key_prefix=handler_prefix_key,
                    kwargs=kwargs,
                )
                handler = self._create_handler(
                    kwargs_key_prefix=handler_prefix_key,
                    kwargs=kwargs,
                    formatter=formatter,
                    default_stream=default_stream,
                )
                self._log.addHandler(handler)
                self.handlers[handler_prefix_key] = handler
            else:
                self.handlers[handler_prefix_key] = None
        self.console_handler = self.handlers["console"]
        self.max_allowed_message_noise_level = kwargs.get(
            "max_allowed_message_noise_level", 0
        )
        self.subprocess_command_prefix = kwargs.get("subprocess_command_prefix", "[$] ")
        self.subprocess_stdout_prefix = kwargs.get("subprocess_stdout_prefix", "")
        self.subprocess_stderr_prefix = kwargs.get("subprocess_stderr_prefix", "")
        self.subprocess_results_prefix = {
            "stdout": self.subprocess_stdout_prefix,
            "stderr": self.subprocess_stderr_prefix,
        }
        self.subprocess_results_color = {
            "stdout": self.theme_colors["process_stdout"],
            "stderr": self.theme_colors["process_stderr"],
        }

    def _log_message(self, msg, log_fn, **kwargs):
        theme_color = kwargs.pop("color", None)
        if theme_color is not None:
            color = self.theme_colors[theme_color]
            msg = color.apply(msg)
        if kwargs.pop("noise_level", 0) <= self.max_allowed_message_noise_level:
            log_fn(msg)

    def apply_theme_color(self, theme_color_name, msg):
        s = self.theme_colors[theme_color_name].apply(msg)
        return s

    def format_indented(
        self,
        msg,
        nlevels=1,
        bullet=None,
        indent_str="    ",
        color=None,
    ):
        if nlevels == 0:
            return s
        if bullet:
            final_indent = "".join([bullet_str, indent_str[len(bullet_str) :]])
        else:
            final_indent = indent_str
        if nlevels > 1:
            preceding_indents = indent_str * (nlevels - 1)
        else:
            preceding_indents = ""
        if msg and color:
            msg = self.theme_colors[color].apply(msg)
        s = "{}{}{}".format(preceding_indents, final_indent, msg)
        return s

    def log_debug(self, msg, **kwargs):
        self._log_message(msg=msg, log_fn=self._log.debug, **kwargs)

    def log_info(self, msg, **kwargs):
        self._log_message(msg=msg, log_fn=self._log.info, **kwargs)

    def log_warning(self, msg, **kwargs):
        self._log_message(msg=msg, log_fn=self._log.warning, **kwargs)

    def log_error(self, msg, **kwargs):
        self._log_message(msg=msg, log_fn=self._log.error, **kwargs)

    def log_critical(self, msg, **kwargs):
        self._log_message(msg=msg, log_fn=self._log.critical, **kwargs)

    def format_as_command(self, cmd):
        s = "{}{}".format(
            self.theme_colors["command_prefix"].apply(self.subprocess_command_prefix),
            self.theme_colors["command"].apply(cmd),
        )
        return s

    def log_banner(self, banner, **kwargs):
        self.log_info(
            f"=== {banner} ===",
            color="banner",
            **kwargs,
        )

    def log_subprocess_command(
        self,
        cmd,
        cwd=None,
        is_coerce_cmd_to_str=True,
        **kwargs
    ):
        m = []
        if cwd:
            if self.subprocess_command_cwd_reporting_style == "pseudocommand":
                m.append(self.format_as_command(f"cd {cwd}"))
            elif self.subprocess_command_cwd_reporting_style == "description":
                self.log_info(
                    "{}{} {}{}".format(
                        self.theme_colors["data"].apply("["),
                        self.theme_colors["data"].apply("Working directory:"),
                        self.theme_colors["path"].apply(cwd),
                        self.theme_colors["data"].apply("]"),
                    ),
                    **kwargs,
                )
            else:
                raise ValueError(self.subprocess_command_cwd_reporting_style)
        if is_coerce_cmd_to_str and not isinstance(cmd, str):
            cmd = " ".join(str(c) for c in cmd)
        if isinstance(cmd, str):
            cmd = [cmd]
        for line in cmd:
            # if not line:
            #     continue
            m.append(self.format_as_command(line))
        self.log_info(m, **kwargs)

    def log_subprocess_results(
        self,
        stdout,
        stderr,
        returncode,
        **kwargs,
    ):
        for skey, stream_results in zip(
            (
                "stdout",
                "stderr",
            ),
            (
                stdout,
                stderr,
            ),
        ):
            if not stream_results:
                continue
            stream_results = self._preprocess_subprocess_results(stream_results)
            color = self.subprocess_results_color[skey]
            lines = []
            for line in stream_results.split("\n"):
                line = line.strip()
                if not line:
                    continue
                line = "{}{}".format(
                    self.theme_colors["command"].apply(
                        self.subprocess_results_prefix[skey]
                    ),
                    self.subprocess_results_color[skey].apply(line),
                )
                lines.append(line)
            self.log_info(lines, **kwargs)

    def _get_format_specification(
        self,
        kwargs_key_prefix,
        kwargs_value_suffix,
        kwargs,
        default,
    ):
        # first check for specific,
        # then check for logger-wide
        # then given default
        k1 = "{}_{}".format(kwargs_key_prefix, kwargs_value_suffix)
        if k1 in kwargs:
            return kwargs[k1]
        k2 = kwargs_value_suffix
        if k2 in kwargs:
            return kwargs[k2]
        else:
            return default

    def _create_formatter(
        self,
        formatter_type,
        kwargs_key_prefix,
        kwargs,
    ):
        # First search logger (root) namespace, prefix = ''.
        # Then update with console/logfile specific namespace: prefixes =
        # 'console_'/'logfile_'
        # If not set at all, class defaults will handle it.
        formatter_kwargs = {}
        formatter_kwargs["name"] = self.name
        formatter_kwargs["logger"] = self
        for prefix in ("", kwargs_key_prefix):
            for value_key in (
                "fmt",
                "datefmt",
                "style",
                "is_colorize",
            ):
                fval = self._get_format_specification(
                    kwargs_key_prefix=prefix,
                    kwargs_value_suffix=value_key,
                    kwargs=kwargs,
                    default=None,
                )
                formatter_kwargs[value_key] = fval
        return formatter_type(**formatter_kwargs)

    def _create_handler(
        self,
        kwargs_key_prefix,
        kwargs,
        formatter,
        default_stream=None,
    ):
        stream = self._get_handler_stream(
            kwargs_key_prefix=kwargs_key_prefix,
            kwargs=kwargs,
            default_stream=default_stream,
        )
        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)
        level = self._get_handler_logging_level(
            kwargs_key_prefix=kwargs_key_prefix,
            kwargs=kwargs,
        )
        handler.setLevel(level)
        return handler

    def _get_handler_stream(self, kwargs_key_prefix, kwargs, default_stream):
        stream_key = "{}_stream".format(kwargs_key_prefix)
        if stream_key in kwargs:
            stream = kwargs[stream_key]
        elif default_stream:
            stream = default_stream
        elif default_stream is not False:
            key = "{}_path".format(kwargs_key_prefix)
            default = self.name + ".log"
            fp = kwargs.get(key, default)
            if fp is None:
                fp = default
            stream = open(fp, "w")
        return stream

    def _get_handler_logging_level(self, kwargs_key_prefix, kwargs):
        kwargs_key = "{}_logging_level".format(kwargs_key_prefix)
        level_name = kwargs.pop(kwargs_key, logging.INFO)
        if level_name in [
            logging.NOTSET,
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]:
            level = level_name
        elif level_name is not None:
            level_name = str(level_name).upper()
        elif _LOGGING_LEVEL_ENVAR in os.environ:
            level_name = os.environ[_LOGGING_LEVEL_ENVAR].upper()
        else:
            level_name = "NOTSET"
        if level_name == "NOTSET":
            level = logging.NOTSET
        elif level_name == "DEBUG":
            level = logging.DEBUG
        elif level_name == "INFO":
            level = logging.INFO
        elif level_name == "WARNING":
            level = logging.WARNING
        elif level_name == "ERROR":
            level = logging.ERROR
        elif level_name == "CRITICAL":
            level = logging.CRITICAL
        else:
            level = logging.NOTSET
        return level

    def _preprocess_subprocess_results(self, s):
        try:
            s = s.decode("utf-8")
        except AttributeError:
            pass
        return s


# }}}1 Logger

# Support {{{1

# Logging Formatters {{{2

# BaseFormatter {{{3


class BaseFormatter(logging.Formatter):

    default_datefmt = "%Y-%m-%d %H:%M:%S"
    default_format_style = "%"
    default_fmt_template = "%(msg)"

    ansi_code_pattern = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    @classmethod
    def strip_ansi_codes(cls, s):
        return cls.ansi_code_pattern.sub("", s)

    def __init__(
        self,
        logger,
        name,
        fmt,
        datefmt=None,
        style=None,
        **kwargs,
    ):
        assert name
        self.logger = logger
        if fmt is None:
            if style is None or style == "%":
                fmt = self.default_fmt_template.format(name=name)
            else:
                raise NotImplementedError(style)
        if datefmt is None:
            datefmt = self.default_datefmt
        if style is None:
            style = self.default_format_style
        self._name = name
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
        )
        self.subsequent_indent = " " * self.get_prefix_len()
        self.is_wrap = False

    def get_prefix_len(self):
        # format dummy message to get prefix length
        message = "!!!COMMANDLOGGER-TAG!!!"
        record = logging.LogRecord(
            self._name,
            level=logging.CRITICAL,
            pathname=__file__,
            lineno=10000,
            msg=message,
            args=None,
            exc_info=None,
            func=None,
            sinfo=None,
        )
        out = super().format(record)
        prefix = out.split(message)[0]
        prefix = self.strip_ansi_codes(prefix)
        return len(prefix)

    def format(self, record):
        record_copy = copy.copy(record)
        self._prepacklines_record(record_copy)
        record_copy.msg = self._pack_lines(record_copy.msg)
        self._postpacklines_record(record_copy)
        self._annotate_message_level(record_copy)
        self._postannotate_record(record_copy)
        return super().format(record_copy)

    def _prepacklines_record(self, record):
        """
        Derived classes should implement any processing of
        log record fields before the base class packs
        the record message. The ``record`` value here is an
        instance-specific *copy* of the record, so any
        modifications will not effect any other handler
        output.
        """
        pass

    def _postpacklines_record(self, record):
        """
        Derived classes should implement any processing of
        log record fields after the base class packs
        the record message. The ``record`` value here is an
        instance-specific *copy* of the record, so any
        modifications will not effect any other handler
        output.
        """
        pass

    def _postannotate_record(self, record):
        """
        Derived classes should implement any processing of
        log record fields after the base class packs
        the record message. The ``record`` value here is an
        instance-specific *copy* of the record, so any
        modifications will not effect any other handler
        output.
        """
        pass

    def _annotate_message_level(self, record):
        annotation = ""
        if record.levelno == logging.DEBUG and self.logger.debug_message_prefix:
            annotation = self.logger.debug_message_prefix
        elif record.levelno == logging.INFO and self.logger.info_message_prefix:
            annotation = self.logger.info_message_prefix
        elif record.levelno == logging.WARNING and self.logger.warning_message_prefix:
            annotation = self.logger.warning_message_prefix
        elif record.levelno == logging.ERROR and self.logger.error_message_prefix:
            annotation = self.logger.error_message_prefix
        elif record.levelno == logging.CRITICAL and self.logger.critical_message_prefix:
            annotation = self.logger.critical_message_prefix
        if annotation:
            annotation = self._postprocess_annotation(annotation)
            if annotation:
                spacer = " "
            else:
                spacer = ""
            record.msg = f"{annotation}{spacer}{record.msg}"

    def _postprocess_annotation(self, annotation):
        return annotation

    def _pack_lines(self, msg):
        """
        Handles lists as multiple lines with indenting.
        """
        if isinstance(msg, str):
            return msg
        parts = []
        if isinstance(msg, str):
            msg_rows = [msg]
        else:
            msg_rows = msg
        for idx, msg_row in enumerate(msg_rows):
            if idx == 0:
                initial_indent = ""
            else:
                initial_indent = self.subsequent_indent
            s = "{}{}".format(initial_indent, msg_row)
            parts.append(s)
        return "\n".join(parts)

# }}}3 BaseFormatter

# ConsoleFormatter {{{3


class ConsoleFormatter(BaseFormatter):

    default_fmt_template = "[{name}] %(msg)s"

    def __init__(self, **kwargs):
        self.is_colorize = kwargs.get("is_colorize", True)
        name = kwargs["name"]
        self.theme_colors = kwargs["logger"].theme_colors
        if not kwargs.get("fmt", None):
            prefix = "[{}]".format(name)
            if self.is_colorize:
                prefix = self.theme_colors["metadata"].apply(prefix)
            kwargs["fmt"] = "{} %(msg)s".format(prefix)
        super().__init__(**kwargs)

    def _postpacklines_record(self, record):
        if not self.is_colorize:
            record.msg = self.strip_ansi_codes(record.msg)
        else:
            if record.levelno == logging.DEBUG:
                record.msg = self.theme_colors["debug"].apply(record.msg)
            elif record.levelno == logging.INFO:
                record.msg = self.theme_colors["info"].apply(record.msg)
            elif record.levelno == logging.WARNING:
                record.msg = self.theme_colors["warning"].apply(record.msg)
            elif record.levelno == logging.ERROR:
                record.msg = self.theme_colors["error"].apply(record.msg)
            elif record.levelno == logging.CRITICAL:
                record.msg = self.theme_colors["critical"].apply(record.msg)

    def _postprocess_annotation(self, annotation):
        if not self.is_colorize:
            annotation = self.strip_ansi_codes(annotation)
        return annotation

# }}}3 ConsoleFormatter

# LogFileFormatter {{{3


class LogFileFormatter(BaseFormatter):

    default_fmt_template = "[{name} %(asctime)s] %(msg)s"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _postpacklines_record(self, record):
        record.msg = self.strip_ansi_codes(record.msg)

    def _postprocess_annotation(self, annotation):
        annotation = self.strip_ansi_codes(annotation)
        return annotation


# }}}3 LogFileFormatter

# }}}2 Formatters

# }}}1 Support
