#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=3: 
#   }}}1
#   Imports: 
#   {{{2
import sys
import datetime
import os
from os.path import expanduser
from pathlib import Path
import importlib
import time
import math
import rumps
import csv
import inspect
import weakref
import logging
import importlib
import pkgutil
#   }}}1
#   {{{2
from decaycalc.decaycalc import DecayCalc
from timeplot.timeplot import TimePlot
#   Usage:
#   located_filepaths = self.timeplot._GetFiles_Monthly(self._data_dir, self.prefix, self.postfix, self.dt_start, self.dt_end, True)
#   results_dt, results_qty = self.timeplot._ReadData(located_filepaths, self.label, self.col_dt, self.col_qty, self.col_label, self.delim)
#   remaining_qty = self.decaycalc.CalculateAtDT(self.dt_analyse, results_dt, results_qty, self.halflife, self.onset)


_log = logging.getLogger('pulse')
_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(level=logging.DEBUG, format=_logging_format, datefmt=_logging_datetime)

class PulseApp(rumps.App):
    timeplot = TimePlot()
    decaycalc = DecayCalc()

    _output_decimals = 2
    _poll_dt = 15

    _delta_now_recent_threshold = 300
    _qty_now_threshold = 0.01

    _data_source_dir = os.environ.get('mld_icloud_workflowDocuments')
    _data_source_filename = 'Schedule.iphone.log'

    _gpgkey_default = "pantheon.redgrey@gpg.key"

    _data_dir = os.environ.get('mld_logs_schedule')
    _datafile_prefix = "Schedule.calc."
    _datafile_postfix = ".vimgpg"

    _poll_items_file = [ 'pulse', 'poll-items.txt' ]
    _poll_cols_file = [ 'pulse', 'poll-columns.txt' ]

    #   cols: [ label, qty, dt ]
    _poll_cols = []

    _poll_labels = []
    _poll_halflives = []
    _poll_onsets = []

    _qty_now = []
    _qty_now_previous = []

    _init_string = "Hello There"

    def __init__(self):
    #   {{{
        _log.debug("start")
        _list_menu = [ 'Today Plot', 'Quit' ]

        super().__init__(self._init_string, menu=_list_menu, quit_button=None)

        if not os.path.isdir(self._data_dir):
            _log.error("not found, _data_dir=(%s)" % str(_data_dir))
            sys.exit(2)

        self.Read_PollCols()
        self.Read_PollItems()

        for loop_label in self._poll_labels:
            self._qty_now.append(0)

        self.timer = rumps.Timer(self.func_poll, self._poll_dt)
        self.timer.start()
    #   }}}

    @rumps.clicked('Quit')
    def handle_quit(self, _):
    #   {{{
        """quit handler"""
        _log.debug("closing now")
        rumps.quit_application()
    #   }}}

    def func_poll(self, sender):
    #   {{{
        _now = datetime.datetime.now()
        _log.debug("_now=(%s)" % str(_now))

        #    def _CopyAndDivideDataByMonth(self, arg_source_path, arg_dest_dir, arg_dest_prefix, arg_dest_postfix, arg_dt_first, arg_dt_last, arg_overwrite=False, arg_includeMonthBefore=False, arg_gpg_key=None):
        try:
            _path_source = os.path.join(self._data_source_dir, self._data_source_filename)
            self.timeplot._CopyAndDivideDataByMonth(_path_source, self._data_dir, self._datafile_prefix, self._datafile_postfix, _now, _now, True, True, self._gpgkey_default)
        except Exception as e:
            _log.error("%s, %s" % (type(e), str(e)))
            raise Exception("failed to copy data")

        self._qty_now_previous = self._qty_now
        self._qty_now = []

        col_delim = ","
        col_label = self._poll_cols[0]
        col_qty = self._poll_cols[1]
        col_dt = self._poll_cols[2]

        last_dt = None
        delta_now = []

        for loop_label, loop_halflife, loop_onset in zip(self._poll_labels, self._poll_halflives, self._poll_onsets):
            _log.debug("loop_label=(%s), loop_halflife=(%s), loop_onset=(%s)" % (str(loop_label), str(loop_halflife), str(loop_onset)))
            try:
                located_filepaths = self.timeplot._GetFiles_Monthly(self._data_dir, self._datafile_prefix, self._datafile_postfix, _now, _now, True)
                data_dt, data_qty = self.timeplot._ReadData(located_filepaths, loop_label, col_dt, col_qty, col_label, col_delim)

                last_dt = sorted(data_dt)[-1]
                delta_now.append((_now - last_dt).total_seconds())

                loop_qty = self.decaycalc.CalculateAtDT(_now, data_dt, data_qty, loop_halflife, loop_onset)
                loop_qty = round(loop_qty, 2)
                self._qty_now.append(loop_qty)
            except Exception as e:
                _log.error("%s, %s" % (type(e), str(e)))

        poll_str = ""
        delta_now_recent_mins = int(sorted(delta_now)[0] / 60)
        if (delta_now_recent_mins < self._delta_now_recent_threshold):
            poll_str += str(delta_now_recent_mins) + "⏳"
        _log.debug("delta_now_recent_mins=(%s)" % str(delta_now_recent_mins))

        try:
            for loop_i, (loop_qty, loop_label) in enumerate(zip(self._qty_now, self._poll_labels)):
                _log.debug("loop_label=(%s), loop_qty=(%s)" % (str(loop_label), str(loop_qty)))
                #_log.debug(self._qty_now_previous[loop_i])
                if (loop_qty >= self._qty_now_threshold):
                    poll_str += str(loop_label[0]) + str(loop_qty)
                    if (loop_qty > self._qty_now_previous[loop_i]):
                        poll_str += "🔺"
                    else:
                        poll_str += " "
        except Exception as e:
            _log.error("%s, %s" % (type(e), str(e)))

        poll_str = poll_str.strip()
        _log.debug("poll_str=(%s)" % str(poll_str))
        self.title = poll_str
    #   }}}

    def Read_PollItems(self):
    #   {{{
        """Read resource file _poll_items_file to _poll_labels, _poll_halflives, _poll_onsets as tab-delimited values"""
        file_poll_items = importlib.resources.open_text(*self._poll_items_file)
        _log.debug("file_poll_items=(%s)" % str(file_poll_items))
        for loop_line in file_poll_items:
            loop_line = loop_line.strip()
            loop_line = loop_line.split("\t")
            if (len(loop_line) > 1):
                self._poll_labels.append(loop_line[0])
                self._poll_halflives.append(60 * int(loop_line[1]))
                self._poll_onsets.append(60 * int(loop_line[2]))
        file_poll_items.close()
        _log.debug("_poll_labels=(%s)" % str(self._poll_labels))
        _log.debug("_poll_halflives=(%s)" % str(self._poll_halflives))
        _log.debug("_poll_onsets=(%s)" % str(self._poll_onsets))
    #   }}}

    def Read_PollCols(self):
    #   {{{
        """Read resource file _poll_cols_file to _poll_cols as tab-delimited integers"""
        file_poll_cols = importlib.resources.open_text(*self._poll_cols_file)
        _log.debug("file_poll_cols=(%s)" % str(file_poll_cols))
        filedata = file_poll_cols.read().strip()
        _poll_cols_str = filedata.split("\t")
        for loop_item in _poll_cols_str:
            self._poll_cols.append(int(loop_item))
        file_poll_cols.close()
        _log.debug("_poll_cols=(%s)" % str(self._poll_cols))
    #   }}}


#   }}}1

