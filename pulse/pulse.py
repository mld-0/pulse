# -*- coding: utf-8 -*-
#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=3: 
#   }}}1
#   Imports: 
#   {{{3
import sys
import datetime
import os
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
import webbrowser
#   }}}1
#   {{{2
from timeplot.decaycalc import DecayCalc
from timeplot.timeplot import TimePlot

_log = logging.getLogger('pulse')
_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(level=logging.DEBUG, format=_logging_format, datefmt=_logging_datetime)

class PulseApp(rumps.App):
    timeplot = TimePlot()
    decaycalc = DecayCalc()

    _output_decimals = 2
    _poll_dt = 15
    _qty_precision = 2
    _delta_now_recent_threshold = 300
    _qty_now_threshold = 0.01

    _data_source_dir = os.environ.get('mld_icloud_workflowDocuments')
    _data_source_filename = 'Schedule.iphone.log'

    _gpgkey_default = "pantheon.redgrey@gpg.key"
    _data_dir = os.environ.get('mld_logs_pulse')
    _plot_dir = os.environ.get('mld_plots_pulse')
    _datafile_prefix = "Schedule.calc."
    _datafile_postfix = ".vimgpg"
    _data_delim = ","

    color_options = [ "blue", "green", "red", "black", "orange" ]

    _poll_items_file = [ 'pulse', 'poll-items.txt' ]
    _poll_cols_file = [ 'pulse', 'poll-columns.txt' ]

    #   cols: [ label, qty, dt ]
    _poll_cols = []
    _poll_labels = []
    _poll_halflives = []
    _poll_onsets = []
    _qty_today = []
    _qty_now = []
    _qty_now_previous = []
    _init_string = "Hello There"

    def __init__(self):
    #   {{{
        _log.debug("start")

        #super().__init__(self._init_string, menu=self._list_menu, quit_button=None)

        super().__init__(self._init_string, quit_button=None)

        self.qtytoday_menu_item = rumps.MenuItem("qty:")
        self.todayplot_menu_item = rumps.MenuItem("Plot Today")
        self.monthplot_menu_item = rumps.MenuItem("Plot Month")
        self.allplot_menu_item = rumps.MenuItem("Plot All")
        self.quit_menu_item = rumps.MenuItem("Quit")
        self.menu.add(self.qtytoday_menu_item)
        self.menu.add(self.todayplot_menu_item)
        self.menu.add(self.monthplot_menu_item)
        self.menu.add(self.allplot_menu_item)
        self.menu.add(self.quit_menu_item)

        if not os.path.isdir(self._data_dir):
            _log.warning("mkdir _data_dir=(%s)" % str(self._data_dir))
            os.mkdir(self._data_dir)

        if not os.path.isdir(self._plot_dir):
            _log.warning("mkdir _plot_dir=(%s)" % str(self._plot_dir))
            os.mkdir(self._plot_dir)

        #   Read parameters from respective files _poll_cols_file, _poll_items_file
        self._ReadResource_Cols()
        self._ReadResource_Items()

        #   Initalise qty list
        for loop_label in self._poll_labels:
            self._qty_now.append(0)
            self._qty_today.append(0)

        self.timer = rumps.Timer(self.func_poll, self._poll_dt)
        self.timer.start()
    #   }}}

    def _Format_QtyToday(self):
    #   {{{
        result_str = "qty: "
        for loop_qty, loop_label in zip(self._qty_today, self._poll_labels):
            result_str += loop_label[0] + str(loop_qty) + " "
        result_str = result_str.strip()
        return result_str
    #   }}}

    #   TODO: 2021-01-13T16:26:19AEDT (how to) show plot figure without application closing when plot is closed
    @rumps.clicked('Plot Today')
    def handle_plotToday(self, _):
    #   {{{
        _log.debug("begin")
        date_start = datetime.datetime.now()
        date_end = datetime.datetime.now()
        #_plot_dir = "/tmp"
        try:
            self.timeplot.AnalyseDataByDaysList(self._data_dir, self._datafile_prefix, self._datafile_postfix, [ date_start, date_end ], self._poll_labels, self._poll_halflives, self._poll_onsets, self._poll_cols[2], self._poll_cols[1], self._poll_cols[0], self._data_delim, self._plot_dir, self.color_options)
            #_path_save = _paths_plot_save[0]
            webbrowser.open('file:%s' % self._plot_dir)
            #   Open plot file itself fails?
            ##  {{{
            #_log.debug("_path_save=(%s)" % str(_path_save))
            #import subprocess, os, platform
            #if platform.system() == 'Darwin':       # macOS
            #    subprocess.call(('open', _path_save))
            #elif platform.system() == 'Windows':    # Windows
            #    os.startfile(_path_save)
            #else:                                   # linux variants
            #    subprocess.call(('xdg-open', _path_save))
            ##   }}}
        except Exception as e:
            _log.error("%s, %s" % (type(e), str(e)))
        _log.debug("done")
        #self.timer = rumps.Timer(self.func_poll, self._poll_dt)
        #self.timer.start()
    #   }}}

    @rumps.clicked('Plot Month')
    def handle_plotMonth(self, _):
    #   {{{
        _log.debug("begin")
        date_month = datetime.datetime.now()
        try:
            self.timeplot.AnalyseDataForMonth(self._data_dir, self._datafile_prefix, self._datafile_postfix, date_month, self._poll_labels, self._poll_halflives, self._poll_onsets, self._poll_cols[2], self._poll_cols[1], self._poll_cols[0], self._data_delim, self._plot_dir, self.color_options)
            webbrowser.open('file:%s' % self._plot_dir)
        except Exception as e:
            _log.error("%s, %s" % (type(e), str(e)))
        _log.debug("done")
    #   }}}

    @rumps.clicked('Plot All')
    def handle_plotAll(self, _):
    #   {{{
        _log.debug("begin")
        date_month = datetime.datetime.now()
        try:
            self.timeplot.AnalyseDataByMonthForAll(self._data_dir, self._datafile_prefix, self._datafile_postfix, self._poll_labels, self._poll_halflives, self._poll_onsets, self._poll_cols[2], self._poll_cols[1], self._poll_cols[0], self._data_delim, self._plot_dir, self.color_options)
            webbrowser.open('file:%s' % self._plot_dir)
        except Exception as e:
            _log.error("%s, %s" % (type(e), str(e)))
        _log.debug("done")
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

        #   Copy any new data from self._data_source_dir to self._data_dir
        try:
            _path_source = os.path.join(self._data_source_dir, self._data_source_filename)
            self.timeplot._CopyAndDivideDataByMonth(_path_source, self._data_dir, self._datafile_prefix, self._datafile_postfix, _now, _now, True, True, self._gpgkey_default)
        except Exception as e:
            _log.error("%s, %s" % (type(e), str(e)))
            raise Exception("failed to copy data")

        self._qty_now_previous = self._qty_now
        self._qty_now = []
        self._qty_today = []

        col_label = self._poll_cols[0]
        col_qty = self._poll_cols[1]
        col_dt = self._poll_cols[2]

        last_dt = None
        delta_now = []

        for loop_label, loop_halflife, loop_onset in zip(self._poll_labels, self._poll_halflives, self._poll_onsets):
            _log.debug("loop_label=(%s), loop_halflife=(%s), loop_onset=(%s)" % (str(loop_label), str(loop_halflife), str(loop_onset)))
            try:
                located_filepaths = self.timeplot._GetFiles_Monthly(self._data_dir, self._datafile_prefix, self._datafile_postfix, _now, _now, True)
                data_dt, data_qty = self.timeplot._ReadData(located_filepaths, loop_label, col_dt, col_qty, col_label, self._data_delim)
                #_log.debug("len(data_dt)=(%s)" % len(data_dt))

                data_dt_sorted = data_dt[:]
                try:
                    data_dt_sorted.sort()
                except Exception as e:
                    pass
                last_dt = data_dt_sorted[-1]
                delta_now.append((_now - last_dt).total_seconds())
                _log.debug("last_dt=(%s)" % str(last_dt))

                loop_qty_today = self.decaycalc.TotalQtyForDay(_now, data_dt, data_qty)
                self._qty_today.append(loop_qty_today)
                loop_qty_now = self.decaycalc.CalculateAtDT(_now, data_dt, data_qty, loop_halflife, loop_onset)
                loop_qty_now = round(loop_qty_now, self._qty_precision)
                self._qty_now.append(loop_qty_now)
            except Exception as e:
                _log.error("%s, %s" % (type(e), str(e)))
                raise Exception("failed to calculate value")

        _log.debug("_qty_today=(%s)" % str(self._qty_today))
        _log.debug("_qty_now=(%s)" % str(self._qty_now))
        _log.debug("delta_now=(%s)" % str(delta_now))

        poll_str_qty = ""
        poll_str_delta = ""
        try:
            for loop_i, (loop_qty_now, loop_label, loop_delta_now) in enumerate(zip(self._qty_now, self._poll_labels, delta_now)):
                _log.debug("loop_label=(%s), loop_qty_now=(%s)" % (str(loop_label), str(loop_qty_now)))
                #_log.debug(self._qty_now_previous[loop_i])
                if (loop_qty_now >= self._qty_now_threshold):
                    poll_str_qty += str(loop_label[0]) + str(loop_qty_now)
                    if (loop_qty_now > self._qty_now_previous[loop_i]):
                        poll_str_qty += "🔺"
                    else:
                        poll_str_qty += " "
                    poll_str_delta += str(int(loop_delta_now / 60)) + " "
        except Exception as e:
            _log.error("%s, %s" % (type(e), str(e)))

        poll_str_qty = poll_str_qty.strip()
        poll_str_delta = poll_str_delta.strip()

        poll_title_str = poll_str_delta + "⏳" + poll_str_qty
        _log.debug("poll_title_str=(%s)" % str(poll_title_str))

        self.qtytoday_menu_item.title = self._Format_QtyToday()
        self.title = poll_title_str
    #   }}}

    def _ReadResource_Items(self):
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

    def _ReadResource_Cols(self):
    #   {{{
        """Read resource file _poll_cols_file to _poll_cols as tab-delimited integers. Columns: [ label, qty, datetime ]"""
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

