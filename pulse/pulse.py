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
import tempfile
import dateutil
import subprocess
import pprint
#   }}}1
#   {{{2
logging.getLogger('matplotlib').setLevel(logging.WARNING)

from dtscan.dtscan import DTScanner
from timeplot.decaycalc import DecayCalc
from timeplot.timeplot import TimePlot
from timeplot.plotdecayqtys import PlotDecayQtys
from timeplot.util import TimePlotUtils
from subprocess import Popen, PIPE, STDOUT

_log = logging.getLogger('pulse')
_logging_format="%(funcName)s: %(levelname)s, %(message)s"
_logging_datetime="%Y-%m-%dT%H:%M:%S%Z"
logging.basicConfig(level=logging.DEBUG, format=_logging_format, datefmt=_logging_datetime)
#logging.getLogger("matplotlib").setLevel(logging.WARNING)


#   TODO: 2021-01-25T21:37:26AEDT pulse, hide matplotlib debug output during startup

#   TODO: 2021-01-25T21:41:41AEDT pulse, as per vimh, menu item with splitsum for day -> for zsh_history -> file itself uses epochs -> must be filtered somehow, excessively long

class PulseApp(rumps.App):
    timeplot = TimePlot()
    decaycalc = DecayCalc()
    plotdecayqtys = PlotDecayQtys()
    dtscanner = DTScanner()

    _path_temp_dir = tempfile.mkdtemp()

    _poll_dt = 30
    _qty_precision = 2
    _qty_now_threshold = 0.01

    #   Update to mld_log_timestamps when said file has been created during loop
    _splitsum_vimh_file = os.environ.get('mld_log_vimh')
    #_splitsum_vimh_file = os.environ.get('mld_log_timestamps')

       
    #_script_combine_timestamps = os.environ.get('mld_combine_timestamps_local')

    _splitsum_split_delta =  300
    _splitsum_label =  'splitsum'

    _datasource_dir = os.environ.get('mld_icloud_workflowDocuments')
    _datasource_filename = 'Schedule.iphone.log'

    _datacopy_dir = os.environ.get('mld_logs_pulse')
    _datacopy_prefix = "Schedule.calc."
    _datacopy_postfix = ".vimgpg"

    _output_plot_dir = os.environ.get('mld_plots_pulse')
    #path_vimh_local = os.environ.get('mld_log_vimh')
    path_sysout_cloud = os.environ.get('mld_out_cloud_shared')

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

        self.qtytodayvimh_menu_item = rumps.MenuItem("qty:")
        self.splitsums_menu_item = rumps.MenuItem("sums:")
        self.todayplot_menu_item = rumps.MenuItem("Plot Schedule Today")
        self.monthplot_menu_item = rumps.MenuItem("Plot Schedule Month")
        self.allplot_menu_item = rumps.MenuItem("Plot Schedule All")
        self.quit_menu_item = rumps.MenuItem("Quit")
        self.menu.add(self.qtytodayvimh_menu_item)
        self.menu.add(self.splitsums_menu_item)
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

        #self._GetVimhElapsedToday()
    #   }}}

    def _Zsh_History_Recent(self):
    #   {{{
        """Get last 1000 items in zsh history file, with iso timestamps, as list-of-strings"""
        _cmd_history = """
        #!/bin/zsh --login
        export HISTFILE=~/.zsh_history 
        export HISTSIZE=1000
        fc -R 
        fc -l -t "%FT%H:%M:%S%Z" 0 | cut -c 8- 
        """
        _cmd_zsh_history = [ '/bin/zsh', '-c', _cmd_history ]
        p = subprocess.Popen(_cmd_zsh_history, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = p.communicate()
        result_history = stdout.split('\n')
        return result_history
    #   }}}
                
    #   TODO: 2021-02-01T17:31:00AEDT add to file path_temp, shell (zsh) history lines for today
    def _GetVimh_SplitSum_Today(self):
    #   {{{
        """Get splits sum (using dtscanner) in file self._splitsum_vimh_file for today"""
        result_str = ""
        today_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        _starttime = datetime.datetime.now()
        _log.debug("today_date_str=(%s)" % str(today_date_str))
        if not (os.path.exists(self._path_temp_dir)):
            os.mkdir(self._path_temp_dir)

        #   Copy lines from loop_filepath to path_temp if they contain today_date_str
        _log.debug("_splitsum_vimh_file\n%s" % str(self._splitsum_vimh_file))
        f = open(self._splitsum_vimh_file, "r")
        #path_temp = os.path.join(self._path_temp_dir, "splitsum.temp.%s" % datetime.datetime.now().strftime("%s.%f"))

        path_temp_unsorted = os.path.join(self._path_temp_dir, "splitsum.temp.unsorted")
        path_temp_sorted = os.path.join(self._path_temp_dir, "splitsum.temp")

        _log.debug("path_temp_unsorted\n%s" % str(path_temp_unsorted))

        result_history = self._Zsh_History_Recent()

        f_temp = open(path_temp_unsorted, "w")
        for loop_line in f:
            if today_date_str in loop_line:
                f_temp.write(loop_line)
        #f_temp.close()
        f.close()

        #   Continue: 2021-02-01T17:43:49AEDT add zsh history entries from today to path_temp. Does path_temp need to be sorted -> tell dtscanner to do so?
        for loop_history_item in result_history:
            if today_date_str in loop_history_item:
                f_temp.write(loop_history_item)
                f_temp.write('\n')
        f_temp.close()

        try:
            #   Sort file path_temp?
            f_sorted = open(path_temp_sorted, "w")
            with open(path_temp_unsorted, 'r') as r:
                for line in sorted(r):
                    f_sorted.write(line)
                    #_log.debug("line=(%s)" % str(line))
            f_sorted.close()
        except Exception as e:
           _log.error("%s, %s, failed to sort path_temp_sorted" % (type(e), str(e)))

        _log.debug("path_temp_sorted\n%s" % str(path_temp_sorted))

        
        #   find splitsum for (lines copied to) path_temp
        try:
            f_sorted = open(path_temp_sorted, "r")

            #   Ongoing: 2021-02-01T21:31:05AEDT presence of datetimes in vimh/zsh history causes date range beyond current day to be analysed -> potential bug) using results from wrong day, potential optimisation) limit splitsum search to current day
            splitsum_results = self.dtscanner.Interface_SplitSum(f_sorted, False, "d", self._splitsum_split_delta, False)

            f_sorted.close()
            _log.debug("splitsum_results=(%s)" % str(splitsum_results))
        except Exception as e:
            _log.error("%s, %s" % (type(e), str(e)))

        #   TODO: 2021-01-25T21:43:18AEDT rather than verifying len(splitsum_results) <= 1, verify date of splitsum_results_last matches today
        if (len(splitsum_results) > 1):
            #   TODO: 2021-02-01T21:42:32AEDT ensure only splitsum results for current day (therefore list of length 1) can be returned from Interface_SplitSum
            #_log.warning("Results from only one day, imply results should only be length 1, len(splitsum_results)=(%s), splitsum_results=(%s)" % (len(splitsum_results), str(splitsum_results)))
            raise Exception("Results from only one day, imply results should only be length 1, len(splitsum_results)=(%s), splitsum_results=(%s)" % (len(splitsum_results), str(splitsum_results)))

        _timedone = datetime.datetime.now()
        _elapsed = _timedone - _starttime
        _log.debug("_elapsed=(%s)" % str(_elapsed))

        try:
            splitsum_results_last = splitsum_results[-1]
            loop_elapsed_str = splitsum_results_last[0]
        except Exception as e:
            _log.error("%s, %s" % (type(e), str(e)))
            loop_elapsed_str = "-"

        #   append to result_str with loop_label and return
        result_str += self._splitsum_label + " " + loop_elapsed_str + " "
        return result_str.strip()
    #   }}}

    def _GetQtys_Sum_Today(self):
    #   {{{
        result_str_label = "qty: "
        result_str = ""
        try:
            for loop_qty, loop_label in zip(self._qty_today, self._data_labels):
                result_str += loop_label[0] + "" + str(loop_qty) + " "
            result_str = result_str.strip()
        except Exception as e:
            _log.debug("%s, %s" % (type(e), str(e)))
            result_str = "-"

        result_str = result_str_label + result_str

        return result_str
    #   }}}

    #   TODO: 2021-01-13T16:26:19AEDT (how to) show plot figure without application closing when plot is closed
    @rumps.clicked('Plot Schedule Today')
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

    @rumps.clicked('Plot Schedule Month')
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

    @rumps.clicked('Plot Schedule All')
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

        self.qtytodayvimh_menu_item.title = self._GetQtys_Sum_Today()
        self.splitsums_menu_item.title = self._GetVimh_SplitSum_Today()

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

