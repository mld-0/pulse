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
import pandas
#   }}}1
#   {{{2
from timeplot.decaycalc import DecayCalc
from timeplot.timeplot import TimePlot
from timeplot.plotdecayqtys import PlotDecayQtys
from timeplot.util import TimePlotUtils

_log = logging.getLogger('pulse')
_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(level=logging.DEBUG, format=_logging_format, datefmt=_logging_datetime)

class PulseApp(rumps.App):
    timeplot = TimePlot()
    decaycalc = DecayCalc()
    plotdecayqtys = PlotDecayQtys()

    _poll_dt = 15
    _qty_precision = 2
    _qty_now_threshold = 0.01

    _datasource_dir = os.environ.get('mld_icloud_workflowDocuments')
    _datasource_filename = 'Schedule.iphone.log'

    _datacopy_dir = os.environ.get('mld_logs_pulse')
    _datacopy_prefix = "Schedule.calc."
    _datacopy_postfix = ".vimgpg"

    _output_plot_dir = os.environ.get('mld_plots_pulse')

    _gpgkey_default = "pantheon.redgrey@gpg.key"
    _data_delim = ","

    _output_plot_colors = [ "blue", "green", "red", "black", "orange" ]

    _data_labels_file = [ 'pulse', 'poll-items.txt' ]
    _data_cols_file = [ 'pulse', 'poll-columns.txt' ]

    #   _data_cols: [ label, qty, dt ] (read from file in that order)
    _data_cols = dict()
    _data_labels = []
    _data_halflives = []
    _data_onsets = []

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

        if not os.path.isdir(self._datacopy_dir):
            _log.warning("mkdir _datacopy_dir=(%s)" % str(self._datacopy_dir))
            os.mkdir(self._datacopy_dir)

        if not os.path.isdir(self._output_plot_dir):
            _log.warning("mkdir _output_plot_dir=(%s)" % str(self._output_plot_dir))
            os.mkdir(self._output_plot_dir)

        #   Read parameters from respective files _data_cols_file, _data_labels_file
        self._ReadResource_DataCols()
        self._ReadResource_DataLabels()

        #   Initalise qty list
        for loop_label in self._data_labels:
            self._qty_now.append(0)
            self._qty_today.append(0)

        self.timer = rumps.Timer(self.func_poll, self._poll_dt)
        self.timer.start()
    #   }}}

    def _Format_QtyToday(self):
    #   {{{
        result_str = "qty: "
        for loop_qty, loop_label in zip(self._qty_today, self._data_labels):
            result_str += loop_label[0] + str(loop_qty) + " "
        result_str = result_str.strip()
        return result_str
    #   }}}

    #   TODO: 2021-01-13T16:26:19AEDT (how to) show plot figure without application closing when plot is closed
    @rumps.clicked('Plot Today')
    def handle_plotToday(self, _):
    #   {{{
        _log.debug("begin")
        try:
            dt_now= datetime.datetime.now()
            webbrowser.open('file:%s' % self._output_plot_dir)

            self.plotdecayqtys.data_file_dir = self._datacopy_dir
            self.plotdecayqtys.data_file_prefix = self._datacopy_prefix
            self.plotdecayqtys.data_file_postfix = self._datacopy_postfix
            self.plotdecayqtys.plot_save_dir = self._output_plot_dir
            self.plotdecayqtys.PlotDaily_DecayQtys_ForDateRange(dt_now, dt_now)
        except Exception as e:
            _log.error("%s, %s" % (type(e), str(e)))
        _log.debug("done")
    #   }}}

    @rumps.clicked('Plot Month')
    def handle_plotMonth(self, _):
    #   {{{
        _log.debug("begin")
        try:
            dt_start = datetime.datetime.now()
            _days_in_month = pandas.Period(dt_start.strftime("%Y-%m-%d")).days_in_month
            dt_start = dt_start.replace(day=1)
            dt_end = dt_start.replace(day=_days_in_month)
            webbrowser.open('file:%s' % self._output_plot_dir)

            self.plotdecayqtys.data_file_dir = self._datacopy_dir
            self.plotdecayqtys.data_file_prefix = self._datacopy_prefix
            self.plotdecayqtys.data_file_postfix = self._datacopy_postfix
            self.plotdecayqtys.plot_save_dir = self._output_plot_dir
            self.plotdecayqtys.PlotDaily_DecayQtys_ForDateRange(dt_start, dt_end)

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
            #self.timeplot.AnalyseDataByMonthForAll(self._datacopy_dir, self._datacopy_prefix, self._datacopy_postfix, self._data_labels, self._data_halflives, self._data_onsets, self._data_cols['datetime'], self._data_cols['qty'], self._data_cols['label'], self._data_delim, self._output_plot_dir, self._output_plot_colors)

            #   Continue: 2021-01-19T15:37:41AEDT set dt_start/dt_end to first/last datetime in log respectively
            located_filepaths = TimePlotUtils._GetAvailableFiles_FromMonthlyRange(self._datacopy_dir, self._datacopy_prefix, self._datacopy_postfix)
            data_dt, data_qty = self.plotdecayqtys._ReadQtyScheduleData(located_filepaths, None)

            dt_start =  data_dt[0]
            dt_end = data_dt[-1]

            webbrowser.open('file:%s' % self._output_plot_dir)

            self.plotdecayqtys.data_file_dir = self._datacopy_dir
            self.plotdecayqtys.data_file_prefix = self._datacopy_prefix
            self.plotdecayqtys.data_file_postfix = self._datacopy_postfix
            self.plotdecayqtys.plot_save_dir = self._output_plot_dir
            self.plotdecayqtys.PlotDaily_DecayQtys_ForDateRange(dt_start, dt_end)

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

        #   Copy any new data from self._datasource_dir to self._datacopy_dir
        try:
            _path_source = os.path.join(self._datasource_dir, self._datasource_filename)
            TimePlotUtils._CopyData_DivideByMonth(_path_source, self._datacopy_dir, self._datacopy_prefix, self._datacopy_postfix, _now, _now, True, True, self._gpgkey_default)
        except Exception as e:
            _log.error("%s, %s" % (type(e), str(e)))
            raise Exception("failed to copy data")

        self._qty_now_previous = self._qty_now
        self._qty_now = []
        self._qty_today = []

        self.plotdecayqtys.data_column_label = self._data_cols['label']
        self.plotdecayqtys.data_column_qty = self._data_cols['qty']
        self.plotdecayqtys.data_column_dt = self._data_cols['datetime']
        self.plotdecayqtys.data_delim = self._data_delim

        last_dt = None
        delta_now = []

        for loop_label, loop_halflife, loop_onset in zip(self._data_labels, self._data_halflives, self._data_onsets):
            _log.debug("loop_label=(%s), loop_halflife=(%s), loop_onset=(%s)" % (str(loop_label), str(loop_halflife), str(loop_onset)))
            try:
                located_filepaths = TimePlotUtils._GetFiles_FromMonthlyRange(self._datacopy_dir, self._datacopy_prefix, self._datacopy_postfix, _now, _now, True)
                data_dt, data_qty = self.plotdecayqtys._ReadQtyScheduleData(located_filepaths, loop_label)
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
            for loop_i, (loop_qty_now, loop_label, loop_delta_now) in enumerate(zip(self._qty_now, self._data_labels, delta_now)):
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

    def _ReadResource_DataLabels(self):
    #   {{{
        """Read resource file _data_labels_file to _data_labels, _data_halflives, _data_onsets as tab-delimited values"""
        file_poll_items = importlib.resources.open_text(*self._data_labels_file)
        _log.debug("file_poll_items=(%s)" % str(file_poll_items))
        for loop_line in file_poll_items:
            loop_line = loop_line.strip()
            loop_line = loop_line.split("\t")
            if (len(loop_line) > 1):
                self._data_labels.append(loop_line[0])
                self._data_halflives.append(60 * int(loop_line[1]))
                self._data_onsets.append(60 * int(loop_line[2]))
        file_poll_items.close()
        _log.debug("_data_labels=(%s)" % str(self._data_labels))
        _log.debug("_data_halflives=(%s)" % str(self._data_halflives))
        _log.debug("_data_onsets=(%s)" % str(self._data_onsets))
    #   }}}

    def _ReadResource_DataCols(self):
    #   {{{
        """Read resource file _data_cols_file to _data_cols as tab-delimited integers. Values (in order): [ label, qty, datetime ]"""
        file_data_cols = importlib.resources.open_text(*self._data_cols_file)
        _log.debug("file_data_cols=(%s)" % str(file_data_cols))
        filedata = file_data_cols.read().strip()
        _data_cols_str = filedata.split("\t")
        self._data_cols['label'] = int(_data_cols_str[0])
        self._data_cols['qty'] = int(_data_cols_str[1])
        self._data_cols['datetime'] = int(_data_cols_str[2])
        file_data_cols.close()
        _log.debug("_data_cols=(%s)" % str(self._data_cols))
    #   }}}


#   }}}1

