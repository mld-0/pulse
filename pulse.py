#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=3: 
#   }}}1
#   Imports: {{{3
import sys
#from datetime import datetime
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
#   }}}1
self_qindex="qindex_cmcat_python_pulse_main"
self_name = "Pulse"
self_printdebug = 0
self_version = "0.1"
self_qreader_py="._qindex_PythonReader.py"
self_qvar_scheduleCalculator = "qindex_script_schedule_calculator_py"
self_qvar_log = "qindex_log_pulse"
self_flag_log = True

#   Imports
#   {{{3
import sys, getopt
import os
from os.path import expanduser
import importlib
from datetime import timedelta 
from datetime import date

from dateutil.tz import tzlocal

from datetime import timedelta, date

import math
from shutil import copyfile
import shutil
import csv
import time
import hashlib
from subprocess import Popen, PIPE, STDOUT

import glob

from io import StringIO
import platform

import inspect
from pathlib import Path

#   }}}1
self_name="PyScheduleCalculator"
self_qindex="qindex_script_schedule_calculator_py"

self_printdebug = 1
self_version = "0.1"
self_delete_tempfile = True

#   If False, only copy data if it contains more lines than destination
self_flag_skip_linecheck = True

#   If False, only copy data if hash of text has not been seen before
self_flag_skip_hashcheck = False

#flag_print_hash_comparision = 0

class ScheduleCalculator(object):
#   {{{3
    _schedule_env_data_copy_dir = 'mld_logs_schedule'
    _schedule_data_source_filename = 'Schedule.iphone.log'

    _schedule_env_data_source_dir = 'mld_icloud_workflowDocuments'

    _schedule_gpgkeyId_default = "pantheon.redgrey@gpg.key"

    #   Variables:
    #qvar__schedule_copiedfile_encrypt = "qval_schedule_copiedfile_encrypt"
    #qvar_copiedfile_prefix = "qval_schedule_copiedfile_prefix"
    #qvar_copiedfile_extension = "qval_schedule_copiedfile_extension"

    _schedule_copiedfile_encrypt = 1
    _schedule_copiedfile_prefix = "Schedule.calc."
    _schedule_copiedfile_postfix = ".vimgpg"
    _schedule_copiedfile_dateformat = "%Y-%m"

    #_schedule_copiedfile_prefix = None
    #_schedule_copiedfile_postfix = None

    _schedule_data_copy_dir = os.environ.get(_schedule_env_data_copy_dir)
    _schedule_data_source_dir = os.environ.get(_schedule_env_data_source_dir)
    _schedule_data_source_path = os.path.join(_schedule_data_source_dir, _schedule_data_source_filename)

    #copiedfile_text_list_str = None
    #copiedfile_text_list_path = None

    copiedfile_hash_dict = None
    copiedfile_text_dict = None
    copiedfile_dict_update_epoch = None

    copylock_file_prefix = "_schedule." 
    copylock_file_postfix = ".copylock"
    copylock_hostname = None
    copylock_timeout_s = 60

    #   #  Import ~/._qindex_PythonReader.py  AS  qindexReader 
    #   #  {{{
    #   filename_qindexReader="._qindex_PythonReader.py"
    #   path_qindexReader = os.path.join(Path.home(), filename_qindexReader)
    #   spec_qindexReader = importlib.util.spec_from_file_location(filename_qindexReader, path_qindexReader)
    #   qindexReader = importlib.util.module_from_spec(spec_qindexReader)
    #   spec_qindexReader.loader.exec_module(qindexReader)
    #   #   }}}

    #   (qvar of) Source file for (all) new data
    #data_source_path_qindexStr="qindex_schedule_file_current"

    #   (qvar of) Directory in which we save new data in a file for the current month (must exist)
    #data_copy_dir_qindexStr="qindex_dir_log_schedule"

    filename_dateStr = None
    filename_dateStr_previous = None
    data_copy_filename = None
    today = None
    first = None
    lastMonth = None
    data_copy_filename_prevous = None
    data_copy_path = None
    data_copy_path_previous = None

    dt_start_date=datetime.datetime(2020,3,3,0,0,0)
    dt_end_date=datetime.datetime(2020,3,3, 23, 59, 59)
    dt_interval_count=200

    halflife_default = 50
    onset_default = 10

    qty_precision_default=3
    analysis_minimum_halflives_default=20

    #   source_filter_(prefix|postfix): strings to affix to begining and end of "yyyy-mm" to create filter for current months data
    source_filter_prefix = ",("
    source_filter_postfix = "-"

    copylock_flag_timeout_delete = True

    #   Functions: 

    #   #   About: 
    #   #   Update: (2020-07-30)-(0257-11) ENTIRELY REDUNDENT?
    #   #   Created: (2020-07-29)-(2207-50)
    #   def LockCopy_Ask(self, copy_dir=None):
    #   #   {{{
    #       func_name = inspect.currentframe().f_code.co_name
    #       global self_printdebug
    #       func_printdebug = self_printdebug
    #       if (copy_dir == None):
    #           copy_dir = self._schedule_data_copy_dir
    #           #   if (func_printdebug == 1):
    #           sys.stderr.write("%s, warning, use default copy_dir=(%s)\n" % (func_name, copy_dir))
    #   #   }}}

    #   Created: (2020-07-30)-(0327-57)
    def touch_file(self, fname):
    #   {{{
        func_name = inspect.currentframe().f_code.co_name
        try:
            os.utime(fname, None)
        except OSError:
            open(fname, 'a').close()
    #   }}}

    #   LockFile filenames are created from system hostname -> No two machines running Pulse via the same cloud share should have the same hostname
    #   Created: (2020-08-30)-(1206-27)
    def Get_Local_LockFile_FileName(self):
    #   {{{
        func_name = inspect.currentframe().f_code.co_name
        _result = self.copylock_file_prefix + self.copylock_hostname + self.copylock_file_postfix 
        return _result
    #   }}}

    #   Remove lockfile belonging to current system if it exists
    #   Created: (2020-08-30)-(1210-28)
    def Delete_Local_LockFile(self, copy_dir=None):
    #   {{{
        func_name = inspect.currentframe().f_code.co_name
        global self_printdebug
        func_printdebug = self_printdebug
        if (copy_dir == None):
            copy_dir = self._schedule_data_copy_dir
            #   if (func_printdebug == 1):
            #sys.stderr.write("%s, warning, use default copy_dir=(%s)\n" % (func_name, copy_dir))
        #   exit if copy_dir is not a valid directory:
        if not os.path.isdir(copy_dir):
            sys.stderr.write("%s, error, invalid dir copy_dir=(%s)\n" % (func_name, str(copy_dir)))
            return 2
        local_lockfile_name = self.Get_Local_LockFile_FileName()
        lockfile_local_path = os.path.join(copy_dir, local_lockfile_name)
        if os.path.exists(lockfile_local_path):
            if (func_printdebug == 1):
                sys.stderr.write("%s, remove lockfile_local_path\n\t%s\n" % (func_name, str(lockfile_local_path)))
            #os.path.remove(lockfile_local_path)
            os.remove(lockfile_local_path)
        else:
            sys.stderr.write("%s, error, lockfile_local_path not found\n\t%s\n" % (func_name, str(lockfile_local_path)))
            return 2

        return 0
    #   }}}

    #   Created: (2020-08-30)-(1215-27)
    def Update_Local_LockFile(self, copy_dir=None, source_epoch_mtime=None):
    #   {{{
        func_name = inspect.currentframe().f_code.co_name
        global self_printdebug
        func_printdebug = self_printdebug
        if (copy_dir == None):
            copy_dir = self._schedule_data_copy_dir
            #   if (func_printdebug == 1):
            sys.stderr.write("%s, warning, use default copy_dir=(%s)\n" % (func_name, copy_dir))
        #   exit if copy_dir is not a valid directory:
        if not os.path.isdir(copy_dir):
            sys.stderr.write("%s, error, invalid dir copy_dir=(%s)\n" % (func_name, str(copy_dir)))
            return 2

        local_lockfile_name = self.Get_Local_LockFile_FileName()
        lockfile_local_path = os.path.join(copy_dir, local_lockfile_name)

        if (source_epoch_mtime is None):
            source_epoch_mtime = self.GetSourceMtime()

        #   Touch lockfile_local_path, then, if the contents of lockfile is not source_epoch_mtime when read and converted to string, replace contents of lockfile with source_epoch_mtime. return 2 with error message if lockfile_local_path doesn't exist after doing so.
        #   {{{
        #if not result_currently_locked:
        if (func_printdebug == 1):
            sys.stderr.write("%s, touch lockfile_local_path\n\t%s\n" % (func_name, str(lockfile_local_path)))

        self.touch_file(lockfile_local_path)

        lockfile_epoch = None
        try:
            with open(lockfile_local_path) as f:
                lockfile_epoch = f.read().strip()
                lockfile_epoch = int(lockfile_epoch)
        except ValueError as e:
            lockfile_epoch = None
            pass
        except Exception as e:
            sys.stderr.write("%s, warning, unexpected %s, %s\n" % (func_name, str(type(e)), str(e)))
        #   }}}
        #   write source_epoch_mtime to lockfile_local_path
        #   {{{
        if (lockfile_epoch is None) or (lockfile_epoch != source_epoch_mtime):
            with open(lockfile_local_path, "w") as f:
                f.write(str(source_epoch_mtime))
        if not os.path.exists(lockfile_local_path):
            sys.stderr.write("%s, error, failed to write lockfile_local_path=(%s)\n" % (func_name, str(lockfile_local_path)))
            return 2
        else:
            return 0
        #   }}}

        #if os.path.exists(lockfile_local_path):
        #    if (func_printdebug == 1):
        #        sys.stderr.write("%s, remove lockfile_local_path\n\t%s\n" % (func_name, str(lockfile_local_path)))
        #    os.path.remove(lockfile_local_path)
        #else:
        #    sys.stderr.write("%s, error, lockfile_local_path not found\n\t%s\n" % (func_name, str(lockfile_local_path)))
        #    return 2
        #
        #return 0
    #   }}}

    #   Created: (2020-07-29)-(2210-05)
    def LockCopy_CheckLocksInDir(self, copy_dir=None):
    #   {{{
        func_name = inspect.currentframe().f_code.co_name
        global self_printdebug
        func_printdebug = self_printdebug
        if (copy_dir == None):
            copy_dir = self._schedule_data_copy_dir
            #   if (func_printdebug == 1):
            sys.stderr.write("%s, warning, use default copy_dir=(%s)\n" % (func_name, copy_dir))
        #   exit if copy_dir is not a valid directory:
        if not os.path.isdir(copy_dir):
            sys.stderr.write("%s, error, invalid dir copy_dir=(%s)\n" % (func_name, str(copy_dir)))
            return 2

        _flag_lockfile_contents_delta_lock = True

        #local_lockfile_name = self.copylock_file_prefix + self.copylock_hostname + self.copylock_file_postfix 
        local_lockfile_name = self.Get_Local_LockFile_FileName()
        lockfile_local_path = os.path.join(copy_dir, local_lockfile_name)

        if (func_printdebug == 1):
            sys.stderr.write("%s, lockfile_local_path=(%s)\n" % (func_name, str(lockfile_local_path)))

        #   Get a list of all possible lock files in copy_dir
        _glob_lockfile = "%s*%s" % (self.copylock_file_prefix, self.copylock_file_postfix)
        _glob_searchpath = os.path.join(copy_dir, _glob_lockfile)
        _glob_results_paths = [ f for f in glob.glob(_glob_searchpath) ]
        _glob_results_basenames = [ os.path.basename(x) for x in _glob_results_paths ]
        #   printdebug:
        #   {{{
        if (func_printdebug == 1):
            sys.stderr.write("%s, _glob_results_basenames=(%s)\n" % (func_name, str(_glob_results_basenames)))
        #   }}}

        #   Seconds since modification of each given lockfile
        lockfiles_mtime_delta = [ self.GetSourceDeltaMtime(x) for x in _glob_results_paths ]

        #   If the contents of the lockfile can be converted to an integer, Add it to lockfiles_epochs, otherwise use None
        #   Said integer is the epoch at which the source file was last updated, according to the machine doing the locking
        lockfiles_epochs = [] 

        #   The modification time of the source file, in epoch format, for comparsion with items in lockfiles_epochs
        source_epoch_mtime = None
        source_epoch_mtime = self.GetSourceMtime()

        #   get time in seconds since last modification

        #   for each lockfile, loop_path, in _glob_results_paths, and the epoch time contained in the file, 
        try:
            for loop_path in _glob_results_paths:
                loop_str = ""
                loop_int = None
                with open(loop_path) as f:
                    loop_str = f.read().strip()
                    try:
                        loop_int = int(loop_str)
                    except ValueError as e:
                        loop_int = None
                        pass
                    lockfiles_epochs.append(loop_int)
                pass
        except Exception as e:
            sys.stderr.write("%s, %s, %s\n" % (func_name, str(type(e)), str(e)))

        #   printdebug:
        #   {{{
        if (func_printdebug == 1):
            _indent = "\t"
            sys.stderr.write("%s\n" % (func_name))
            sys.stderr.write("%slockfiles_mtime_delta=(%s)\n" % (_indent, str(lockfiles_mtime_delta)))
            sys.stderr.write("%slockfiles_epochs=(%s)\n" % (_indent, str(lockfiles_epochs)))
        #   }}}

        result_currently_locked = False
        loop_i=0
        if (func_printdebug == 1):
            sys.stderr.write("%s\n" % (func_name))

        for loop_lockfile_mtime_delta in lockfiles_mtime_delta:
            loop_lockfile_basename = _glob_results_basenames[loop_i]
            loop_lockfile_local_path = _glob_results_paths[loop_i]
            loop_lockfile_epoch = lockfiles_epochs[loop_i]

            lockfile_source_delta = int(loop_lockfile_epoch) - int(source_epoch_mtime)
            #sys.stderr.write("%ssource_epoch_mtime, loop_lockfile_epoch\n\t\t%s\n\t\t%s\n" % (_indent, str(source_epoch_mtime), str(loop_lockfile_epoch)))
            if (func_printdebug == 1):
                sys.stderr.write("%ssource_epoch_mtime=(%s)\n" % (_indent, str(source_epoch_mtime)))
                sys.stderr.write("%sloop_lockfile_epoch=(%s)\n" % (_indent, str(loop_lockfile_epoch)))
                sys.stderr.write("%slockfile_source_delta=(%s)\n" % (_indent, str(lockfile_source_delta)))
            #if not (loop_lockfile_basename == local_lockfile_name):
            if (loop_lockfile_mtime_delta < self.copylock_timeout_s):
                result_currently_locked = True
                #   printdebug:
                #   {{{
                if (func_printdebug == 1):
                    sys.stderr.write("%slock active, delta=(%s), basename=(%s)\n" % (_indent, str(loop_lockfile_mtime_delta), str(loop_lockfile_basename)))
                #   }}}
            else:
                #if (loop_lockfile_epoch is None) or (source_epoch_mtime >= loop_lockfile_epoch):
                if (loop_lockfile_epoch is None) or (int(source_epoch_mtime) >= int(loop_lockfile_epoch)):
                    #   printdebug:
                    #   {{{
                    if (func_printdebug == 1):
                        sys.stderr.write("%slock inactive, delta=(%s), basename=(%s)\n" % (_indent, str(loop_lockfile_mtime_delta), str(loop_lockfile_basename)))
                    #   }}}
                    if self.copylock_flag_timeout_delete:
                        self.Delete_Local_LockFile(copy_dir)
                        ##   printdebug:
                        ##   {{{
                        #if (func_printdebug == 1):
                        #    sys.stderr.write("%sdelete, delta=(%s), loop_lockfile_local_path=(%s)\n" % (_indent, str(loop_lockfile_mtime_delta),str(loop_lockfile_local_path)))
                        ##   }}}
                        #os.remove(loop_lockfile_local_path)
                        ##os.path.remove(loop_lockfile_local_path)
                else:
                    sys.stderr.write("%swarning, expired lock contains newer epoch value than mtime source, _flag_lockfile_contents_delta_lock=(%s), loop_lockfile_basename=(%s), loop_lockfile_epoch=(%s), source_epoch_mtime=(%s)\n" % (_indent, str(_flag_lockfile_contents_delta_lock), str(loop_lockfile_basename), str(loop_lockfile_epoch), str(source_epoch_mtime)))
                    if (_flag_lockfile_contents_delta_lock):
                        result_currently_locked = True
            loop_i += 1

        #   Bugfix: (2020-08-30)-(1558-12) only call Update_Local_LockFile() if result_currently_locked is false, and return 0
        if not result_currently_locked: 
            self.Update_Local_LockFile(copy_dir, source_epoch_mtime)
            return 0

        ##   touch lockfile_local_path
        ##   {{{
        #if not result_currently_locked:
        #    self.touch_file(lockfile_local_path)
        #    #   If the contents of lockfile is not source_epoch_mtime when read and converted to string, replace contents of lockfile with source_epoch_mtime
        #    lockfile_epoch = None
        #    try:
        #        with open(lockfile_local_path) as f:
        #            lockfile_epoch = f.read().strip()
        #            lockfile_epoch = int(lockfile_epoch)
        #    except ValueError as e:
        #        lockfile_epoch = None
        #        pass
        #    except Exception as e:
        #        sys.stderr.write("%s, warning, unexpected %s, %s\n" % (func_name, str(type(e)), str(e)))
        #    #   }}}
        #    #   write source_epoch_mtime to lockfile_local_path
        #    #   {{{
        #    if (lockfile_epoch is None) or (lockfile_epoch != source_epoch_mtime):
        #        with open(lockfile_local_path, "w") as f:
        #            f.write(str(source_epoch_mtime))
        #    if not os.path.exists(lockfile_local_path):
        #        sys.stderr.write("%s, error, failed to write lockfile_local_path=(%s)\n" % (func_name, str(lockfile_local_path)))
        #        return 2
        #    else:
        #        return 0
        #    #   }}}
        if (func_printdebug == 1):
            sys.stderr.write("\n")
        return 2

    #   }}}

    #   {{{
    #   About: Take a filepath as a string, decrypt said file using the system gpg keychain, and return the contents as a string
    #   Args:
    #       file_path, string containing path to file to be decrypted 
    #   Added: (2020-07-23)-(1030-21) add to qindex_script_schedule_calculator_py
    #   Labeled: (2020-05-14)-(1721-08)
    #   }}}
    def CmcatUtil_ReadGPGFile_ToString(self, file_path):
    #   {{{
        global self_printdebug
        flag_exit_on_empty_gpgin = False
        func_name = inspect.currentframe().f_code.co_name
        func_printdebug = self_printdebug
        t_start = time.time()
        #   gpg deccrypt arguments
        cmd_gpg_decrypt = ["gpg", "-q", "--decrypt", file_path]
        #   {{{
        p = Popen(cmd_gpg_decrypt, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        result_data_decrypt, result_stderr = p.communicate()
        result_str = result_data_decrypt.decode()
        result_stderr = result_stderr.decode()
        #   }}}

        file_path_hash = self.sha256sum_file(file_path)
        self.copiedfile_text_dict[file_path] = result_str
        self.copiedfile_hash_dict[file_path] = file_path_hash
        self.copiedfile_dict_update_epoch[file_path] = time.time()

        file_path_basename = os.path.basename(file_path)
        t_end = time.time()
        t_elapsed = round(t_end - t_start, 2)
        if (func_printdebug == 1):
            sys.stderr.write("%s, dt=(%s), decrypt=(%s)\n" % (func_name, str(t_elapsed), file_path_basename))
        #   error/warning if empty:
        result_str_len = len(result_str)
        #if (func_printdebug == 1):
        #    sys.stderr.write("result_str_len=(%s)\n" % str(result_str_len))
        if (result_str_len == 0) and (flag_exit_on_empty_gpgin == True):
            sys.stderr.write("%s, error, gpg decrypt result_str empty\n" % (func_name))
            return None
        #elif (result_str_len == 0):
        #    sys.stderr.write("%s, warning, gpg decrypt result_str empty\n" % (func_name))

        #self.copiedfile_text_list_str.append(result_str)
        #self.copiedfile_text_list_path.append(file_path)

        return result_str
    #   }}}

    #   {{{
    #   About: Take a string, encrypt that string with the system gpg keychain, and return result as a bytearray
    #   Args: 
    #       text_str, string to be encrypted
    #       gpg_key_id, string describing gpg key. default=pantheon.redgrey@gpg.key
    #       flag_ascii_armor, if true, 
    #   Added: (2020-07-23)-(1030-15) add to qindex_script_schedule_calculator_py
    #   Labeled: (2020-05-14)-(1808-50)
    #   }}}
    def CmcatUtil_EncryptGPG_String2Bytes(self, text_str, gpg_key_id=None, flag_ascii_armor=False):
    #   {{{
        global self_printdebug
        func_printdebug = self_printdebug
        func_name = inspect.currentframe().f_code.co_name
        t_start = time.time()
        #   default gpg_key_id if none given
        #   {{{
        if (gpg_key_id is None) or (len(gpg_key_id) == 0):
            gpg_key_id = self._schedule_gpgkeyId_default
            if (func_printdebug == 1):
                sys.stderr.write("use gpg key default=(%s)\n" % str(gpg_key_id))
        #   }}}
        #   convert string(text_str) -> bytearray(cmd_encrypt_input)
        #   {{{
        cmd_encrypt_input = bytearray()
        cmd_encrypt_input.extend(text_str.encode())
        #   }}}
        #   gpg encrypt arguments
        #   {{{
        cmd_gpg_encrypt = [ "gpg", "-o", "-", "-q", "--encrypt", "--recipient", gpg_key_id ]
        if (flag_ascii_armor == True):
            cmd_gpg_encrypt.append("--armor")
        #   }}}
        #   Use Popen, call cmd_gpg_encrypt, using PIPE for stdin/stdout/stderr
        #   {{{
        p = Popen(cmd_gpg_encrypt, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        result_data_encrypt, result_stderr = p.communicate(input=cmd_encrypt_input)
        result_stderr = result_stderr.decode()
        #   }}}
        t_end = time.time()
        t_elapsed = round(t_end - t_start, 2)
        if (func_printdebug == 1):
            sys.stderr.write("%s, encrypt dt=(%s)\n" % (func_name, str(t_elapsed)))
        #   printdebug:
        #   {{{
        if (func_printdebug == 1):
            sys.stderr.write("cmd_gpg_encrypt=(%s)\n" % str(cmd_gpg_encrypt))
            sys.stderr.write("result_stderr=(%s)\n" % str(result_stderr))
            sys.stderr.write("text_str_len=(%s)\n" % str(len(text_str)))
            sys.stderr.write("result_data_encrypt_len=(%s)\n" % str(len(result_data_encrypt)))
        #   }}}
        return result_data_encrypt
    #   }}}


    #   About: Read contents of path_source, encrypt with CmcatUtil_EncryptGPG_String2Bytes, and write to path_destination
    #   Created: (2020-07-23)-(1035-20)
    def CmcatUtil_EncryptGPG_CopyFileEncrypt(self, path_source, path_destination):
    #   {{{
        global self_printdebug
        func_printdebug = self_printdebug
        func_name = inspect.currentframe().f_code.co_name
        t_start = time.time()
        source_text = ""
        with open(path_source, 'r') as f:
            for line in f:
                source_text += line

        source_encrypt = self.CmcatUtil_EncryptGPG_String2Bytes(source_text)
        source_hash = self.sha256sum_string(source_encrypt)

        #self.copiedfile_text_list_str.append(source_text)
        #self.copiedfile_text_path.append(file_path)
        self.copiedfile_text_dict[path_source] = source_text
        self.copiedfile_hash_dict[path_source] = source_hash
        self.copiedfile_dict_update_epoch[path_source] = time.time()

        #path_file = open(path_destination, "wb")
        with open(path_destination, "wb") as path_file:
            path_file.write(source_encrypt)
        t_end = time.time()
        t_elapsed = round(t_end - t_start)
        if (func_printdebug == 1):
            sys.stderr.write("%s, copy dt=(%s)\n" % (func_name, str(t_elapsed)))

    #   }}}

    #   About: Get data from last month as well as the current month, to deal with the situation where items from both the current and previous month are still in effect. Items from before a month ago are presumed to be inactive.
    #   {{{
    #   Created: (2020-07-01)-(1227-18)
    #   }}}
    def UpdatePathVars(self):
    #   {{{

        func_name = inspect.currentframe().f_code.co_name
        #global self.filename_dateStr 
        #global self.data_copy_filename 
        #global self.today 
        #global self.first 
        #global self.lastMonth 
        #global self.filename_dateStr_previous 
        #global self.data_copy_filename_prevous 
        #global self._schedule_data_source_path 
        #global self._schedule_data_copy_dir
        #global self.data_copy_path 
        #global self.data_copy_path_previous 
        #global _schedule_copiedfile_encrypt
        ##global self._schedule_copiedfile_dateformat
        #global self._schedule_copiedfile_prefix    
        #global self.copiedfile_extension_text 
        #global self.copiedfile_extension_encrypted

        self.copylock_hostname = platform.node()

        #if (self.copiedfile_text_list_str is None):
        #    self.copiedfile_text_list_str = []
        #if (self.copiedfile_text_list_path is None):
        #    self.copiedfile_text_list_path = []

        if (self.copiedfile_text_dict is None):
            self.copiedfile_text_dict = { }
            self.copiedfile_hash_dict = { }
            self.copiedfile_dict_update_epoch = { }

        self.today = date.today()
        self.first = self.today.replace(day=1)
        self.lastMonth = self.first - timedelta(days=1)

        #self.filename_dateStr = datetime.now().strftime("%Y-%m")
        #self.filename_dateStr_previous = self.lastMonth.strftime("%Y-%m")

        self.filename_dateStr = datetime.datetime.now().strftime(self._schedule_copiedfile_dateformat)
        self.filename_dateStr_previous = self.lastMonth.strftime(self._schedule_copiedfile_dateformat)
        extension = ""

        #self.data_copy_filename="Schedule.calculator." + self.filename_dateStr + ".log"
        #self.data_copy_filename_prevous = "Schedule.calculator." + self.filename_dateStr_previous + ".log"

        #self._schedule_copiedfile_encrypt = self.qindexReader.get_var(self.qvar__schedule_copiedfile_encrypt)
        #self._schedule_copiedfile_encrypt = int(self._schedule_copiedfile_encrypt)
        #self._schedule_copiedfile_prefix = self.qindexReader.get_var(self.qvar_copiedfile_prefix)
        #self._schedule_copiedfile_postfix = self.qindexReader.get_var(self.qvar_copiedfile_extension)

        #extension = self._schedule_copiedfile_postfix
        #if (self._schedule_copiedfile_encrypt == 1):
        #    extension = self.copiedfile_extension_encrypted

        self.data_copy_filename = self._schedule_copiedfile_prefix + self.filename_dateStr + self._schedule_copiedfile_postfix
        self.data_copy_filename_prevous = self._schedule_copiedfile_prefix  + self.filename_dateStr_previous + self._schedule_copiedfile_postfix

        #self._schedule_data_source_path = self.qindexReader.get_var(self.data_source_path_qindexStr)
        #self._schedule_data_copy_dir = self.qindexReader.get_var(self.data_copy_dir_qindexStr)

        self.data_copy_path = os.path.join(self._schedule_data_copy_dir, self.data_copy_filename)
        self.data_copy_path_previous = os.path.join(self._schedule_data_copy_dir, self.data_copy_filename_prevous)

        try:
            if not (os.path.exists(self._schedule_data_copy_dir)):
                sys.stderr.write("%s, create dir\n\t%s" % (func_name, str(self._schedule_data_copy_dir)))
                os.mkdir(self._schedule_data_copy_dir)
        except Exception as e:
            sys.stderr.write("%s, %s, %s\n" % (func_name, str(type(e)), str(e)))

    #   }}}


    #   Function:
    #   About: Get a list of self.dt_interval_count evenly spaced datetimes, that are between startdate and enddate, inclusive
    def DateTimeRange_ByStartEndAndCount(self, startdate, enddate, arg_dt_interval_count):
    #   {{{
        arg_dt_interval_count = arg_dt_interval_count-1
        dateList = []
        #base = datetime.self.today()
        if (type(startdate) == "string"):
            start = datetime.datetime.strptime(startdate, "%Y-%m-%d")
        else:
            start = startdate
        if (type(enddate) == "string"):
            end = datetime.datetime.strptime(enddate, "%Y-%m-%d")
        else:
            end = enddate 
        delta_seconds=(end-start).total_seconds()
        interval_seconds = delta_seconds/arg_dt_interval_count
        date_list = [start + timedelta(seconds=math.ceil(interval_seconds*x)) for x in range(arg_dt_interval_count+1)]
        #for date_item in date_list:
        #    print(date_item.strftime("%F %H:%M:%S"))
        return date_list
    #   }}}

    def DateRange_ByStartAndCount(self, startdate_str, day_count):
    #   {{{
        dateList = []
        #base = datetime.self.today()
        if (type(startdate_str) == "string"):
            base = datetime.datetime.strptime(startdate_str, "%Y-%m-%d")
        else:
            base = startdate_str
        if (day_count < 0):
            day_count = day_count * -1
            date_list = [base - timedelta(days=x) for x in range(day_count)]
        else:
            date_list = [base + timedelta(days=x) for x in range(day_count)]
        return date_list
        #for date_item in date_list:
        #    print(date_item.strftime("%F"))
    #   }}}

    def ScheduleCalc_DTSAlt2DateTime(self, dts_str):
    #   {{{
    #   Updated: (2020-04-10)-(1821-46) Support Both formats: (%Y)-(%H%M-%S) and (%Y)-(%H-%M-%S)
        global self_printdebug
        func_printdebug = self_printdebug

        func_printdebug = 0

        dts_list=dts_str.replace("(", "").replace(")", "").split("-")
        if (len(dts_list) >= 6):
            dts_year=dts_list[0]; dts_year_int=int(dts_year);
            dts_month=dts_list[1]; dts_month_int=int(dts_month);
            dts_day=dts_list[2]; dts_day_int=int(dts_day);
            dts_hour=dts_list[3]; dts_hour_int=int(dts_hour);
            dts_min=dts_list[4]; dts_min_int=int(dts_min);
            dts_sec=dts_list[5]; dts_sec_int=int(dts_sec);
        elif (len(dts_list) == 5):
            dts_year=dts_list[0]; dts_year_int=int(dts_year);
            dts_month=dts_list[1]; dts_month_int=int(dts_month);
            dts_day=dts_list[2]; dts_day_int=int(dts_day);
            dts_hour=dts_list[3][0:2]; dts_hour_int=int(dts_hour);
            dts_min=dts_list[3][2:4]; dts_min_int=int(dts_min);
            dts_sec=dts_list[4]; dts_sec_int=int(dts_sec);

        else:
            if (func_printdebug == 1):
                message_str = "Failed to convert " + str(dts_str)
                print(message_str)
            return 0
        if (func_printdebug == 1):
            message_str = "Convert: " + str(dts_str) + " -> "
            message_str += dts_year + "-" + dts_month + "-" + dts_day + ", " + dts_hour + ":" + dts_min + ":" + dts_sec
            print(message_str)
        dts_datetime = datetime.datetime(dts_year_int, dts_month_int, dts_day_int, dts_hour_int, dts_min_int, dts_sec_int)
        return dts_datetime
    #   }}}

    #   About: Copy (replace) file at self.data_copy_path with contents of file at self._schedule_data_source_path
    #   {{{
    #   Update: (2020-09-12)-(1802-44) Bugfix, copying from source_path to source_filtered_path, fix linecount of source_filtered
    #   Update: (2020-09-12)-(1651-06) Add line count comparison between copy_path and source_filtered_path, add self_flag_skip_(linecheck|hash)
    #   Update: (2020-08-29)-(2005-31) Create empty file copy_path if it does not exit -> bugfix
    #   Labeled: (2020-07-23)-(0923-32)
    #   }}}
    def LocalCopyScheduleData(self, date_filter, source_path=None, copy_path=None):
    #   {{{
        func_name = inspect.currentframe().f_code.co_name
        global self_printdebug
        global self_delete_tempfile
        global self_flag_skip_linecheck
        global self_flag_skip_hashcheck
        func_printdebug = self_printdebug
        t_start = time.time()

        if (copy_path is None):
            copy_path = self.data_copy_path
            sys.stderr.write("%s, warning, arg=None, use default copy_path=(%s)\n" % (func_name, copy_path))
        if (source_path is None):
            source_path = self._schedule_data_source_path
            sys.stderr.write("%s, warning, arg=None, use default source_path=(%s)\n" % (func_name, source_path))

        copy_path_dirname = os.path.dirname(copy_path)

        if (func_printdebug == 1):
            sys.stderr.write("%s, copy_path_dirname=(%s)\n" % (func_name, str(copy_path_dirname)))

        result_lockcopy = 0
        try:
            result_lockcopy = self.LockCopy_CheckLocksInDir(copy_path_dirname)
        except Exception as e:
            sys.stderr.write("%s, %s, %s\n" % (func_name, str(type(e)), str(e)))

        if (func_printdebug == 1):
            sys.stderr.write("%s, result_lockcopy=(%s)\n" % (func_name, str(result_lockcopy)))
        if not (result_lockcopy == 0):
            #if (func_printdebug == 1):
            sys.stderr.write("%s, skip copy, result_lockcopy=(%s)\n" % (func_name, result_lockcopy))
            return 2

        source_filtered_path = ""
        dir_tmp = "/tmp"
        source_path_basename = os.path.basename(source_path)
        source_filtered_filename = ".copy." + source_path_basename
        source_filtered_path = os.path.join(dir_tmp, source_filtered_filename)

        source_data = ""
        source_data_lines = 0

        source_filter_datestr = datetime.datetime.now().strftime(date_filter)
        source_filter_dateformatstr = "%Y-%m"
        source_filter_datestr = datetime.datetime.now().strftime(source_filter_dateformatstr)
        source_filter = self.source_filter_prefix + source_filter_datestr  + self.source_filter_postfix

        #   Add lines of source_path to source_data if they contain source_filter_datestr, and write result to source_filtered_path
        #   {{{
        with open(source_path) as f:
            for loop_line in f:
                if (source_filter in loop_line):
                    source_data += loop_line 
        source_data_lines = source_data.count("\n")

        try:
            with open(source_filtered_path, "w") as f:
                _result = f.write(source_data)
        except Exception as e:
            sys.stderr.write("%s, %s\n" % (str(type(e)), str(e)))
        #   }}}

        if (func_printdebug == 1):
            sys.stderr.write("%s, source_filter=(%s)\n" % (func_name, source_filter))

        #   printdebug:
        #   {{{
        if (func_printdebug == 1):
            #sys.stderr.write("%s, source_path_lines=(%s)\n" % (func_name, str(source_path_lines)))
            sys.stderr.write("%s, source_data_lines=(%s)\n" % (func_name, str(source_data_lines)))
            sys.stderr.write("%s, _result=(%s), source_filtered_path=(%s)\n" % (func_name, str(_result), str(source_filtered_path)))
        #   }}}

        source_filtered_hash = self.sha256sum_file(source_filtered_path)
        source_filtered_lines = 0
        try:
            source_filtered_lines = sum(1 for line in open(source_filtered_path))
        except Exception as e:
            sys.stderr.write("%s, %s, %s\n" % (func_name, str(type(e)), str(e)))

        if (source_filtered_lines == 0):
            sys.stderr.write("%s, warning, source_filtered_lines=(%s)\n" % (func_name, str(source_filtered_lines)))

        #   Hash contents of file as string -> we can do the same with the decrypted contents of gpg file?
        #   Update: (2020-08-29)-(1953-31) create file copy_path if it does not exist 
        copy_lines = 0
        copy_hash = ""
        if (self._schedule_copiedfile_encrypt == 0):
            if not os.path.exists(copy_path):
                sys.stderr.write("%s, create file copy_path=(%s)\n" % (func_name, str(copy_path)))
                self.touch_file(copy_path)
            copy_hash = self.sha256sum_file(copy_path)
        else:
            if not os.path.exists(copy_path):
                sys.stderr.write("%s, create gpg file copy_path=(%s)\n" % (func_name, str(copy_path)))
                try:
                    _new_file_str = ""
                    _new_file_gpgstr = self.CmcatUtil_EncryptGPG_String2Bytes(_new_file_str)
                    with open (copy_path, "wb") as f:
                        f.write(_new_file_gpgstr)
                except Exception as e:
                    sys.stderr.write("%s, error, failed to create gpg file copy_path=(%s), %s, %s\n" % (func_name, str(copy_path), str(type(e)), str(e)))

            copy_file_str = self.CmcatUtil_ReadGPGFile_ToString(copy_path)
            copy_lines = len(copy_file_str.splitlines())
            copy_hash = self.sha256sum_string(copy_file_str)
        if (copy_lines == 0):
            sys.stderr.write("%s, warning, copy_lines=(%s)\n" % (func_name, str(copy_lines)))

        t_end = time.time()
        t_elapsed = round(t_end - t_start, 2)
        if (func_printdebug == 1):
            sys.stderr.write("%s, check dt=(%s)\n" % (func_name, str(t_elapsed)))

        if (func_printdebug == 1):
            sys.stderr.write("\tcopy_path=(%s)\n" % str(copy_path))
            sys.stderr.write("\tsource_path=(%s)\n" % str(source_path))
            sys.stderr.write("\tsource_filtered_hash=(%s)\n" % source_filtered_hash)
            sys.stderr.write("\tcopy_hash=(%s)\n" % copy_hash)
            sys.stderr.write("\tsource_filtered_lines=(%s)\n" % source_filtered_lines)
            sys.stderr.write("\tcopy_lines=(%s)\n" % copy_lines)


        #   (Disabled) flag_delete_previous
        #   {{{
        #flag_delete_previous = False
        #   Update: (2020-07-23)-(0948-01) If (files at) copy_path and source_path have different (hash?), replace copy_path with source_path? Also, if/when we want to add gpg, compare the hash of the source_file, with the hash of the decrypted contents of copy_path (which ought be a match?)
        #if (os.path.exists(copy_path) and flag_delete_previous == True):
        #    if (func_printdebug == 1):
        #        sys.stderr.write("delete copy_path=%s\n" % copy_path)
        #    os.remove(copy_path)
        #copy_path_temp = "/tmp/schedule.data.tmp"
        #copy_path_encrypt = copy_path + ".vimgpg"
        #   }}}

        source_filtered_lines = len(open(source_filtered_path).readlines())


        #   Update copy_path if source_filtered_lines > copy_lines and source_filtered_hash != copy_hash
        #   {{{
        if (source_filtered_lines > copy_lines) or (self_flag_skip_linecheck):
            if (source_filtered_hash != copy_hash) or (self_flag_skip_hashcheck):
                if (func_printdebug == 1):
                    sys.stderr.write("hashes not matched, copying\n")
                if (self._schedule_copiedfile_encrypt == 0):
                    shutil.copy(source_filtered_path, copy_path)
                else:
                    self.CmcatUtil_EncryptGPG_CopyFileEncrypt(source_filtered_path, copy_path)
            else:
                if (func_printdebug == 1):
                    sys.stderr.write("hashes matched, skip copy\n")
        else:
            if (func_printdebug == 1):
                sys.stderr.write("%s, skip copy, source_filtered_lines=(%s), copy_lines=(%s)\n" % (func_name, str(source_filtered_lines), str(copy_lines)))
        #   }}}

        #   Delete source_path if self_delete_tempfile is True
        #   {{{
        if (self_delete_tempfile):
            try:
                if (func_printdebug == 1):
                    sys.stderr.write("%s, delete source_filtered_path=(%s)\n" % (func_name, str(source_filtered_path)))
                os.remove(source_filtered_path)
            except Exception as e:
                sys.stderr.write("%s, %s, %s\n" % (func_name, str(type(e)), str(e)))
        #   }}}

        #   printdebug: Trailing newline
        #   {{{
        if (func_printdebug == 1):
            sys.stderr.write("\n")
        #   }}}

    #   }}}

    #   Labeled: (2020-07-24)-(0958-49)
    def sha256sum_file(self, filename):
    #   {{{
        if not (os.path.exists(filename)):
            return ""
        h  = hashlib.sha256()
        b  = bytearray(128*1024)
        mv = memoryview(b)
        with open(filename, 'rb', buffering=0) as f:
            for n in iter(lambda : f.readinto(mv), 0):
                h.update(mv[:n])
        return h.hexdigest()
    #   }}}

    #   Labeled: (2020-07-24)-(0958-43)
    def sha256sum_string(self, arg_str):
    #   {{{
        if (type(arg_str) != str):
            arg_str = str(arg_str)
        hs = hashlib.sha256(arg_str.encode('utf-8')).hexdigest()
        return hs
    #   }}}

    #   Labeled: (2020-08-19)-(1738-29)
    def GetSourceMtime(self, source_path=None):
    #   {{{
        if (source_path is None):
            source_path = self._schedule_data_source_path
        #   Ongoing: (2020-08-19)-(1739-04) Need to convert to integer?
        result = os.path.getmtime(source_path) 
        return int(result)
    #   }}}

    #   Labeled: (2020-08-19)-(1738-29)
    def GetSourceDeltaMtime(self, source_path=None):
    #   {{{
        if (source_path is None):
            #global self._schedule_data_source_path
            source_path = self._schedule_data_source_path
        #   source_mtime_delta: Number of seconds between now, and the last m-time of the file at self._schedule_data_source_path 
        source_mtime_delta = round(time.time() - os.path.getmtime(source_path))
        return source_mtime_delta
    #   }}}

    #   TODO: (2020-04-11)-(1711-43) ScheduleCalc_Seconds2DHMS doesn't add leading zeros
    def ScheduleCalc_Seconds2DHMS(self, seconds):
    #   {{{
        dhms_str = ""
        D = int(seconds/60/60/24)
        H = int(seconds/60/60%24)
        M = int(seconds/60%60)
        S = int(seconds%60)
        if (D > 0):
            dhms_str += str(D) + "d"
        if (H > 0):
            dhms_str += str(H) + "h"
        if (M > 0):
            dhms_str += str(M) + "m"
        if (S > 0):
            dhms_str += str(S) + "s"
        return dhms_str
    #   }}}

    #   Read log data values that are within our date range, date_datafilterRange, into list analysis_log_data and return said list
    #   Update: (2020-07-24)-(1033-47) If the file contains gpg data, use CmcatUtil_ReadGPGFile_ToString to read
    #   Labeled: (2020-07-24)-(1033-44)
    def GetAnalysisLogData(self, data_filepath, filter_date_start, filter_date_len):
    #   {{{
        func_name = inspect.currentframe().f_code.co_name
        global self_printdebug
        func_printdebug = self_printdebug

        analysis_log_data = []

        date_datafilterRange = self.DateRange_ByStartAndCount(filter_date_start, filter_date_len)

        data_str = ""

        data_filepath_basename = os.path.basename(data_filepath)
        filepath_hash = self.sha256sum_file(data_filepath)
        if (data_filepath in self.copiedfile_text_dict):
            try:
                if (filepath_hash == self.copiedfile_hash_dict[data_filepath]):
                    if (func_printdebug == 1):
                        sys.stderr.write("%s, read at (%s) from (%s)\n" % (func_name, str(round(self.copiedfile_dict_update_epoch[data_filepath])), str(data_filepath_basename)))
                    data_str = self.copiedfile_text_dict[data_filepath]
            except Exception as e:
                sys.stderr.write("%s, e=(%s)\n" % (func_name, str(e)))
                data_str = ""

        if (len(data_str) == 0):
            if (self._schedule_copiedfile_encrypt == 0):
                with open(data_filepath) as f:
                    for f_line in f:
                        data_str += f_line
            else:
                data_str = self.CmcatUtil_ReadGPGFile_ToString(data_filepath)
                #self.copiedfile_text_list_str.append(data_str)
                #self.copiedfile_text_list_path.append(data_filepath)

            self.copiedfile_text_dict[data_filepath] = data_str
            self.copiedfile_hash_dict[data_filepath] = filepath_hash
            self.copiedfile_dict_update_epoch[data_filepath] = time.time()

        #with open(data_filepath) as fd:
        fd = StringIO(data_str)
        rd = csv.reader(fd, delimiter=",")
        for loop_row in rd:
            loop_row_len=len(loop_row)
            if (loop_row_len > 1):
                loop_dts_str = loop_row[3] 
                loop_datetime = self.ScheduleCalc_DTSAlt2DateTime(loop_dts_str)
                loop_name_str = loop_row[0]
                loop_qty_str = loop_row[1]
                loop_unit_str = loop_row[2]
                loop_list = [ loop_datetime , loop_name_str, loop_qty_str, loop_unit_str, loop_dts_str ]
                #loop_message_str = str(loop_datetime) + ", " + loop_name_str + ", " + loop_qty_str

                if (loop_datetime > date_datafilterRange[-1] and loop_datetime < date_datafilterRange[0]):
                    analysis_log_data.append(loop_list)

        return analysis_log_data
    #   }}}

    #   About: Return (python datetime) of last entry in log, for a given analysis_filter (i.e: D-IR, Can), (or epoch=0 (1970) if not found?)
    #   {{{
    #   Created: (2020-07-13)-(1400-29)
    #   }}}
    def TimeOfFinalInstance(self, analysis_filter):
    #   {{{
        date_now = datetime.datetime.now()
        daterange_len = -3
        if (os.path.isfile(self.data_copy_path)):
            analysis_log_data = self.GetAnalysisLogData(self.data_copy_path, date_now, daterange_len)
        else:
            print("Fail, self.data_copy_path=(%s) not found" % (self.data_copy_path))
            sys.exit()
        final_time = datetime.datetime(1970,1,1)
        for log_line in analysis_log_data:
            if (log_line[1].find(analysis_filter) >= 0):
                loop_datetime = log_line[0]
                if (loop_datetime > final_time):
                    final_time = loop_datetime
        return final_time
    #   }}}


    #   Labeled: (2020-07-23)-(0933-37)
    def QtyAtTime(self, analysis_time, analysis_filter, analysis_log_data, half_life_mins, onset_mins, qty_precision=None, analysis_minimum_halflives=None):
    #   {{{
        if (analysis_minimum_halflives is None):
            #global self.analysis_minimum_halflives_default
            analysis_minimum_halflives = self.analysis_minimum_halflives_default

        if (qty_precision is None):
            #global self.qty_precision_default
            qty_precision = self.qty_precision_default

        global self_printdebug
        func_printdebug = self_printdebug
        qty_remaining = 0
        for log_line in analysis_log_data:
            #   Not just exact matches, search for substring
            if (log_line[1].find(analysis_filter) >= 0):
            #if (log_line[1].find(analysis_filter) >= 0 or analysis_filter.find(log_line[1]) >= 0):
            #if (log_line[1] == analysis_filter):
                loop_datetime = log_line[0]
                loop_qty = float(log_line[2])
                loop_time_delta_mins = (analysis_time - loop_datetime).total_seconds() / 60.0
                #if (loop_time_delta_mins > 0):
                if (loop_time_delta_mins > 0 and loop_time_delta_mins < onset_mins):
                    onset_fraction = loop_time_delta_mins / onset_mins
                    #print("onset_fraction=(%s)" % (onset_fraction))
                    loop_qty_remaining = 0
                    exponent = (loop_time_delta_mins - onset_mins) / half_life_mins
                    #exponent = (loop_time_delta_mins) / half_life_mins
                    loop_qty_remaining = onset_fraction * loop_qty * (0.5 ** exponent)
                    qty_remaining += loop_qty_remaining
                elif (loop_time_delta_mins > onset_mins and loop_time_delta_mins < half_life_mins * analysis_minimum_halflives):
                    #print("loop_time_delta_mins=(%s)" % (loop_time_delta_mins))
                    loop_qty_remaining = 0
                    exponent = (loop_time_delta_mins - onset_mins) / half_life_mins
                    loop_qty_remaining = loop_qty * (0.5 ** exponent)
                    qty_remaining += loop_qty_remaining
                    #if (func_printdebug == 1 and loop_qty_remaining > 1):
                        #print("datetime=(%s), qty=(%s), delta_secs=(%s), qty_r=(%s)" % (loop_datetime, loop_qty, loop_time_delta_mins, loop_qty_remaining))
                else:
                    #half_lives_elapsed = loop_time_delta_mins / half_life_mins
                    #print("half_lives_elapsed=(%s)" % (half_lives_elapsed))
                    qty_remaining += 0
        qty_remaining = round(qty_remaining, qty_precision)
        return qty_remaining
    #   }}}


    def QtyForRange(self, analysis_filter, analysis_log_data, half_life_mins, onset_mins, start_date=None, end_date=None, intervals=None):
    #   {{{
        if (start_date is None):
            #global self.dt_start_date
            start_date = self.dt_start_date
        if (end_date is None):
            #global self.dt_end_date
            end_date = self.dt_end_date
        if (intervals is None):
            #global self.dt_interval_count
            intervals = self.dt_interval_count

        print_results = 1
        date_analysisRange_Results = []
        date_analysisRange = self.DateTimeRange_ByStartEndAndCount(start_date, end_date, intervals)
        if (len(date_analysisRange) > 1):
            #print("date_analysisRange Start: (%s)" % (date_analysisRange[0]))
            #print("date_analysisRange End: (%s)" % (date_analysisRange[-1]))
            for date_item in date_analysisRange:
                #loop_qty = QtyAtTime(date_item, arg_filter, analysis_log_data, arg_halflife, arg_onset)
                loop_qty = self.QtyAtTime(date_item, analysis_filter, analysis_log_data, half_life_mins, onset_mins)
                date_analysisRange_Results.append(loop_qty)
            if (len(date_analysisRange) == len(date_analysisRange_Results)):
                loop_i=0
                while (loop_i < len(date_analysisRange)):
                    loop_time_str = date_analysisRange[loop_i].strftime("(%F)-(%H%M-%S)")
                    loop_qty_str = str(date_analysisRange_Results[loop_i])
                    if (print_results == 1):
                        print("%s\t%s" % (loop_time_str, loop_qty_str))
                    loop_i += 1
            else:
                print("Mismatch")
                print(len(date_analysisRange))
                print(len(date_analysisRange_Results))
            return date_analysisRange_Results
        else:
            print("Error, date_analysisRange=(%s)" % (date_analysisRange))
            sys.exit()
        #   On doing a dt_range calculator, here we generate the date range:
        #dt_range = DateTimeRange_ByStartEndAndCount(start_date, end_date,self.dt_interval_count)
        #dt_range_len=len(dt_range)
    #   }}}

        #   #   Process Arguments:
        #   #   {{{
        #   #       -h  Help
        #   #       -f  Filter
        #   arg_dts = ""
        #   arg_filter = ""
        #   arg_include_mtime = 0
        #   arg_halflife = 0
        #   arg_onset = 0
        #   arg_now = 0
        #   arg_start = 0
        #   arg_end = 0
        #   arg_dt_count = 0
        #   try:
        #       opts, args = getopt.getopt(argv, "hNmf:d:o:H:S:E:i:", ["help", "now", "modify", "filter=", "date=", "onset=", "halflife=", "start=", "end=", "intervals="])
        #   }}}
    #   Function: main()
    #   History:
    #   {{{
    #   Note: (2020-05-23)-(0054-18) Disable call to LocalCopyScheduleData for previous months file. 
    #   Labeled: (2020-05-23)-(0054-05)
    #   }}}
    def main(self, argv):
    #   {{{
        global self_printdebug
        func_printdebug = self_printdebug
        self.UpdatePathVars()
        datetime_now=datetime.datetime.now()
        #LocalCopyScheduleData(self.filename_dateStr, self._schedule_data_source_path, self.data_copy_path)
        #   Disable for all but the current month
        #   LocalCopyScheduleData(self.filename_dateStr_previous, self._schedule_data_source_path, self.data_copy_path_previous)
        date_datafilterRange_start=datetime.datetime.now()
        date_datafilterRange_len=-3
        date_analysisRange_start = 0
        date_analysisRange_end = 0
        date_analysisRange_intervalCount = 0
        date_analysisRange = 0
        #   Continue: (2020-05-27)-(2336-17) Get 
        qty = 0
        #   Process Arguments:
        #       -h  Help
        #       -f  Filter
        arg_dts = ""
        arg_filter = ""
        arg_include_mtime = 0
        arg_halflife = 0
        arg_onset = 0
        arg_now = 0
        arg_start = 0
        arg_end = 0
        arg_dt_count = 0
        flag_disable_print = 0
        flag_freeze_check_copy_data = 0
        try:
            opts, args = getopt.getopt(argv, "dhNmf:d:o:H:S:E:i:PF", ["debug", "help", "now", "modify", "filter=", "date=", "onset=", "halflife=", "start=", "end=", "intervals=", "printoff", "freezecopy"])
        except getopt.GetoptError as e:
            print("<ERROR MESSAGE>")
            print(e)
            sys.exit(2)
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print("<HELP MESSAGE>")
                sys.exit()
            elif opt in ("-d", "--debug"):
                self_printdebug = 1
                func_printdebug = 1
            elif opt in ("-f", "--filter"):
                arg_filter = arg
            elif opt in ("-m", "--modify"):
                arg_include_mtime = 1
            elif opt in ("-d", "--date"):
                arg_dts = arg
            elif opt in ("-o", "--onset"):
                arg_onset = float(arg)
            elif opt in ("-H", "--halflife"):
                arg_halflife = float(arg)
            elif opt in ("-N", "--now"):
                arg_now = 1
            elif opt in ("-S", "--start"):
                arg_start = arg
            elif opt in ("-E", "--end"):
                arg_end = arg
            elif opt in ("-i", "--intervals"):
                arg_dt_count = int(arg)
            elif opt in ("-P", "--printoff"):
                flag_disable_print = 1
            elif opt in ("-F", "--freezecopy"):
                flag_freeze_check_copy_data = 1
        if (func_printdebug == 1):
            #print("Args: arg_filter=(%s), arg_now=(%s), arg_include_mtime=(%s), arg_dts=(%s), arg_onset=(%s), arg_halflife=(%s)" % (arg_filter, arg_now, arg_include_mtime, arg_dts, arg_onset, arg_halflife))
            sys.stderr.write("Args: arg_filter=(%s), arg_now=(%s), arg_include_mtime=(%s), arg_dts=(%s), arg_onset=(%s), arg_halflife=(%s)\n" % (arg_filter, arg_now, arg_include_mtime, arg_dts, arg_onset, arg_halflife))
        if (arg_halflife == 0):
            arg_halflife = self.halflife_default
        if (arg_onset == 0):
            arg_onset = self.onset_default
        if (arg_include_mtime == 1):
            file_mtime = self.GetSourceDeltaMtime()
            file_mtime_dhms = self.ScheduleCalc_Seconds2DHMS(file_mtime)
            sys.stderr.write("%s\b" % (file_mtime_dhms))
            return
        if (flag_freeze_check_copy_data != 1):
            try:
                self.LocalCopyScheduleData(self.filename_dateStr, self._schedule_data_source_path, self.data_copy_path)
            except Exception as e:
                sys.stderr.write("%s, %s, %s\n" % (func_name, str(type(e)), str(e)))
        if not (len(arg_filter) == 0):
            qty = self.QtyAtTime
        else:
            sys.stderr.write("Error, need filter\n")
            sys.exit()
        #   Get data from the log files for the current and previous month
        #   {{{
        self.touch_file(self.data_copy_path)
        analysis_log_data = []
        if (os.path.isfile(self.data_copy_path)):
            analysis_log_data = self.GetAnalysisLogData(self.data_copy_path, date_datafilterRange_start, date_datafilterRange_len)
        else:
            print("Fail, self.data_copy_path=(%s) not found" % (self.data_copy_path))
            sys.exit()
        #   Update: (2020-07-23)-(0941-03) (Wait a minute), analysis_log_data_previous is being gotten for a reason, 
        #   {{{
        #   Deprecated: (2020-05-27)-(2329-23) analysis_log_data_previous, on the basis of not being used for anything. Having done so, we are not doing anything wiht any file other than the current month -> edgecase of self.first day(s) of month not handeled.
        #   Ongoing: (2020-05-02)-(1838-04) Fixing the erroneous values produced by poll_now?
        #   }}}
        analysis_log_data_previous = []
        if (os.path.isfile(self.data_copy_path_previous)):
            analysis_log_data_previous = self.GetAnalysisLogData(self.data_copy_path_previous, date_datafilterRange_start, date_datafilterRange_len)
        analysis_log_data = analysis_log_data + analysis_log_data_previous
        #   }}}
        if (arg_now == 1):
            qty = self.QtyAtTime(datetime_now, arg_filter, analysis_log_data, arg_halflife, arg_onset)
            if (flag_disable_print != 1):
                print("%s" % (qty))
            if (func_printdebug == 1):
                sys.stderr.write("\n")
            return qty
        elif not (arg_start == 0 and arg_end == 0):
            #   TODO: (2020-04-11)-(1626-01) Convert to dates, and run for date range.
            date_analysisRange_start = self.ScheduleCalc_DTSAlt2DateTime(arg_start)
            date_analysisRange_end = self.ScheduleCalc_DTSAlt2DateTime(arg_end)
            date_analysisRange_intervalCount = arg_dt_count
            if not (date_analysisRange_start == 0 and date_analysisRange_intervalCount == 0 and date_analysisRange_end):
                result = self.QtyForRange(arg_filter, analysis_log_data, arg_halflife, arg_onset, date_analysisRange_start, date_analysisRange_end, date_analysisRange_intervalCount)
                #   Ongoing: (2020-08-19)-(1809-59) How we want to print/return range-results
                #print(str(result))
                if (func_printdebug == 1):
                    sys.stderr.write("\n")
                return result
                #date_analysisRange = DateTimeRange_ByStartEndAndCount(date_analysisRange_start, date_analysisRange_end, date_analysisRange_intervalCount)
                #if (len(date_analysisRange) > 1):
                #    print("date_analysisRange Start: (%s)" % (date_analysisRange[0]))
                #    print("date_analysisRange End: (%s)" % (date_analysisRange[-1]))
                #    for date_item in date_analysisRange:
                #        #loop_qty = QtyAtTime(date_item, arg_filter, analysis_log_data, arg_halflife, arg_onset)
                #        loop_qty = QtyAtTime(date_item, arg_filter, analysis_log_data, arg_halflife, arg_onset)
                #        date_analysisRange_Results.append(loop_qty)
                #    if (len(date_analysisRange) == len(date_analysisRange_Results)):
                #        loop_i=0
                #        while (loop_i < len(date_analysisRange)):
                #            loop_time_str = date_analysisRange[loop_i].strftime("(%F)-(%H%M-%S)")
                #            loop_qty_str = str(date_analysisRange_Results[loop_i])
                #            print("%s\t%s" % (loop_time_str, loop_qty_str))
                #            loop_i += 1
                #    else:
                #        print("Mismatch")
                #        print(date_analysisRange)
                #        print(date_analysisRange_Results)
                #else:
                #    print("Error, date_analysisRange=(%s)" % (date_analysisRange))
                #    sys.exit()
            else:
                print("date_analysisRange_start=(%s) date_analysisRange_end=(%s) date_analysisRange_intervalCount=(%s)" % (date_analysisRange_start, date_analysisRange_end, date_analysisRange_intervalCount))
        else:
            print("<SPECIFY DATE RANGE (-S <dts>, -E <dts>) OR NOW (-N)>")
        #if (func_printdebug == 1):
            #sys.stderr.write("\n")
    #   }}}


#   }}}1

#if __name__ == "__main__":
#    sc = ScheduleCalculator()
#    sc.main(sys.argv[1:])

rumps.debug_mode(True)

#class PulseApp(object):
class PulseApp(rumps.App):
#   {{{2
    #   Class Variables: 
    _pulse_output_decimals = 2
    update_delta_M_max = 300
    update_delta_M_digits = 1
    poll_qty_threshold = 0.01

    #  3 is our default value, the actual value comes from "poll_dt_var = 'mldsp_schedule_poll_dt'"
    poll_dt = 5  

    DIR_delta_sign_previous = 0
    Can_delta_sign_previous = 0

    #   IMPORT ~/._qindex_PythonReader.py  AS  qindexReader
    #filename_qindexReader = "._qindex_PythonReader.py"
    #filename_qindexReader = None
    #  {{{
    path_qindexReader = "" #os.path.join(Path.home(), filename_qindexReader)
    spec_qindexReader = "" #importlib.util.spec_from_file_location(filename_qindexReader, path_qindexReader)
    qindexReader = None # importlib.util.module_from_spec(spec_qindexReader)
    #   }}}

    #   IMPORT qPath_scheduleCalculator AS scheduleCalc_import
    #qVar_scheduleCalculator = "qindex_script_schedule_calculator_py"
    #   {{{
    #qPath_scheduleCalculator = qindexReader.get_var(qVar_scheduleCalculator)
    qPath_scheduleCalculator = "" # qindexReader.get_var(qVar_scheduleCalculator)
    #spec_scheduleCalc = importlib.util.spec_from_file_location("schedule.Calc", qPath_scheduleCalculator)
    spec_scheduleCalc = None
    #scheduleCalc_import = importlib.util.module_from_spec(spec_scheduleCalc)
    _import_scheduleCalc = None
    #spec_scheduleCalc.loader.exec_module(scheduleCalc_import)
    #   }}}

    scheduleCalc = None
    #qVar_unix_schedule = "qindex_unix_schedule"
    path_log_edges = "/tmp/pulse-edges.log"


    path_log_peaks = os.path.join(Path.home(), ".pulse-peaks.log")

    #   Get DTS for current datetime
    datetime_format_str="(%Y-%m-%d)-(%H%M-%S)"
    #datetime_now = None
    dts_now = ""

    #   TODO: (2020-09-12)-(1552-01) Replace hard-coded DIR, Can, variables, with itterable datastructure, arbitrary length and contents, read from config file
    DIR_args = []
    Can_args = []
    DIR_qty_previous = 0
    Can_qty_previous = 0
    DIR_qty_now = 0 #scheduleCalc_import.main(DIR_args)
    Can_qty_now = 0 #scheduleCalc_import.main(Can_args)
    DIR_delta_sign = 0
    Can_delta_sign = 0

    #   Do not display pulse_deltafile elapsed value if it the 'current time' value is more than pulse_deltafile_split_seconds ago
    pulse_deltafile_split_seconds = 5 * 60

    #   Schedule qtys smaller than poll_qty_threshold are rounded down to zero

    #   Edge Notifications Variables:
    qvar_pulse_edges_DIR = "qindex_pulse_edges_DIR"
    #qpath_pulse_edges_DIR = ""
    edges_list_DIR = [ 3.5, 5.0, 6.5, 8.0 ]
    edge_status_DIR = None
    flag_notify_edges_DIR = True
    flag_notifiy_falling_edges = True
    flag_notify_rising_edges = False

    flag_deltafile_elapsed_min = True

    #   Print time since last D-IR item
    flag_DIR_delta = True
    flag_Can_Delta = True

    poll_epoch = 0
    poll_count = 0


    def CmcatUtil_DTS2EpochTime(self, dts_str):
    #   {{{
        from datetime import datetime
        func_printdebug=0
        dts_list=dts_str.replace("(", "").replace(")", "").split("-")
        dts_year=dts_list[0]; dts_year_int=int(dts_year);
        dts_month=dts_list[1]; dts_month_int=int(dts_month);
        dts_day=dts_list[2]; dts_day_int=int(dts_day);
        dts_hour=dts_list[3][0:2]; dts_hour_int=int(dts_hour);
        dts_min=dts_list[3][2:4]; dts_min_int=int(dts_min);
        dts_sec=dts_list[4]; dts_sec_int=int(dts_sec);
        if (func_printdebug == 1):
            message_str = "Convert: " + str(dts_str) + " -> "
            message_str += dts_year + "-" + dts_month + "-" + dts_day + ", " + dts_hour + ":" + dts_min + ":" + dts_sec
            print(message_str)
        dts_datetime = datetime.datetime(dts_year_int, dts_month_int, dts_day_int, dts_hour_int, dts_min_int, dts_sec_int)
        dts_datetime_seconds = dts_datetime.strftime("%s")
        return dts_datetime_seconds
    #   }}}

    def ReadVars_Schedule(self):
    #   {{{
        func_name = inspect.currentframe().f_code.co_name
        global self_qvar_log

        #   TODO: 2020-11-16T19:40:06AEDT read variables from <>

        self.DIR_onset = 20 
        self.DIR_HL = 50
        self.DIR_filter = "D-IR"
        self.Can_onset = "3"
        self.Can_HL = "35"
        self.Can_filter = "Can-S"

        self.DIR_args = [ "--printoff", "--now", "--filter", str(self.DIR_filter), "--onset", str(self.DIR_onset), "--halflife", str(self.DIR_HL) ]
        self.Can_args = [ "--printoff", "--now", "--filter", str(self.Can_filter), "--onset", str(self.Can_onset), "--halflife", str(self.Can_HL), "--freezecopy" ]
#   }}}

    def __init__(self):
    #   {{{
        global self_qreader_py
        global self_qvar_scheduleCalculator
        #   initialise self.<*> variables with qindexReader:    
        #   {{{
        ##self.filename_qindexReader = self_qreader_py
        ##self.path_qindexReader = os.path.join(Path.home(), self.filename_qindexReader)
        #self.path_qindexReader = os.path.join(Path.home(), self_qreader_py)
        ##self.spec_qindexReader = importlib.util.spec_from_file_location(self.filename_qindexReader, self.path_qindexReader)
        #self.spec_qindexReader = importlib.util.spec_from_file_location(self_qreader_py, self.path_qindexReader)
        #self.qindexReader = importlib.util.module_from_spec(self.spec_qindexReader)
        #self.spec_qindexReader.loader.exec_module(self.qindexReader)

        #self.qPath_schedule_unix = self.qindexReader.get_var(self.qVar_unix_schedule)

        #self.qPath_scheduleCalculator = self.qindexReader.get_var(self.qVar_scheduleCalculator)
        #self.qPath_scheduleCalculator = self.qindexReader.get_var(self_qvar_scheduleCalculator)
        #self.spec_scheduleCalc = importlib.util.spec_from_file_location("schedule.Calc", self.qPath_scheduleCalculator)
        #self.scheduleCalc_import = importlib.util.module_from_spec(self.spec_scheduleCalc)
        #self.spec_scheduleCalc.loader.exec_module(self.scheduleCalc_import)

        self.scheduleCalc = ScheduleCalculator()

        dts_now = datetime.datetime.now().strftime(self.datetime_format_str)
        #   }}}

        #   Moved to ReadVars_Schedule()
        self.ReadVars_Schedule()

        global self_name
        _list_menu = [ 'Quit' ]
        _app_name = "Pulse"

        super().__init__("Hello There", menu=_list_menu, quit_button=None)
        self.timer = rumps.Timer(self.func_poll, self.poll_dt)
        self.timer.start()

        #message_str = "Done __init__()\n"
        #self.WriteLogEdges(message_str)
    #   }}}

    #   About: Handle closure, call scheduleCalc.Delete_Local_LockFile()
    #   Created: (2020-08-30)-(1239-41)
    @rumps.clicked('Quit')
    def clean_up_before_quit(self, _):
    #   {{{
        global self_name
        func_name = inspect.currentframe().f_code.co_name
        sys.stderr.write("\n")
        self.scheduleCalc.Delete_Local_LockFile()
        sys.stderr.write("%s, closing NOW %s\n" % (func_name, str(self_name)))
        rumps.quit_application()
    #   }}}

    #   Get the epoch of the first dts on the first line in qPath_pulse_deltafile
    #   qPath_pulse_deltafile = $qindex_pulse_deltafile_inhome
    def pulse_delta_file(self):
    #   {{{
        global self_printdebug
        func_printdebug = self_printdebug
        pulse_deltafile_lineone_str = ""
        deltafile_delim = '\t'
        try:
            with open(self.qPath_pulse_deltafile, encoding="utf8") as fileopen:
                pulse_deltafile_lineone_str = fileopen.read()
        except Exception as e:
            sys.stderr.write("e=(%s)\n" % str(e))

        pulse_deltafile_lineone_str = pulse_deltafile_lineone_str.strip()
        pulse_deltafile_lineone_list = pulse_deltafile_lineone_str.split(deltafile_delim)

        pulse_deltafile_dts_start = ""
        pulse_deltafile_dts_end = ""
        pulse_deltafile_count = 0 
        pulse_deltafile_elapsed = 0
        try:
            pulse_deltafile_dts_start = pulse_deltafile_lineone_list[0]
            pulse_deltafile_dts_end = pulse_deltafile_lineone_list[1]
            pulse_deltafile_count = int(pulse_deltafile_lineone_list[2])
            pulse_deltafile_elapsed = pulse_deltafile_lineone_list[3]
        except Exception as e:
            sys.stderr.write("e=(%s)\n" % str(e))

        if (func_printdebug == 1):
            sys.stderr.write("pulse_deltafile_lineone_list\n(%s)\n" % str(pulse_deltafile_lineone_list))
            sys.stderr.write("pulse_deltafile_lineone_str=(%s)\n" % str(pulse_deltafile_lineone_str))

        pulse_deltafile_epoch_start = ""
        pulse_deltafile_epoch_end = ""

        try:
            pulse_deltafile_epoch_start = self.CmcatUtil_DTS2EpochTime(pulse_deltafile_dts_start)
            pulse_deltafile_epoch_end = self.CmcatUtil_DTS2EpochTime(pulse_deltafile_dts_end)
        except Exception as e:
            sys.stderr.write("e=(%s)\n" % str(e))

        if (func_printdebug == 1):
            sys.stderr.write("pulse_deltafile_epoch_start=(%s)\n" % str(pulse_deltafile_epoch_start))
            sys.stderr.write("pulse_deltafile_epoch_end=(%s)\n" % str(pulse_deltafile_epoch_end))
            sys.stderr.write("pulse_deltafile_count=(%s)\n" % str(pulse_deltafile_count))
            sys.stderr.write("pulse_deltafile_elapsed=(%s)\n" % str(pulse_deltafile_elapsed))

        return [ pulse_deltafile_epoch_start, pulse_deltafile_epoch_end, pulse_deltafile_count, pulse_deltafile_elapsed ]

    #   }}}

    def CmcatUtil_Seconds2DHMS(self, seconds):
    #   {{{
        global self_printdebug
        func_printdebug = self_printdebug
        seconds_in=seconds
        seconds=int(seconds)
        dts_str=""
        if (seconds < 0):
            dts_str="-"
            seconds = seconds * -1
        D = int(seconds/60/60/24)
        H = int(seconds/60/60%24)
        M = int(seconds/60/60%24)
        M = int(seconds/60%60)
        S = int(seconds%60)
        if (D != 0):
            dts_str += "{:d}d".format(D)
        if (H != 0): 
            if (len(dts_str) == 0):
                dts_str += "{:d}h".format(H)
            else:
                dts_str += "{:02d}h".format(H)
        if (M != 0): 
            if (len(dts_str) == 0):
                dts_str += "{:d}m".format(M)
            else:
                dts_str += "{:02d}m".format(M)
        if (S != 0):
            if (len(dts_str) == 0):
                dts_str += "{:d}s".format(S)
            else:
                dts_str += "{:02d}s".format(S)
        if (len(dts_str) == 0):
            dts_str = "0s"
        if (func_printdebug == 1):
            sys.stderr.write("seconds2dhms: (%s) -> (%s)\n" % (seconds_in, dts_str))
        return dts_str
    #   }}}

    def WriteLogPeaks(self, message_str):
        datetime_str = datetime.datetime.now(tzlocal()).strftime("%Y-%m-%dT%H:%M:%S%Z")
        _delim = "\t"
        output_str = datetime_str + _delim + message_str + "\n"
        sys.stderr.write("output_str=(%s)" % str(output_str))
        with open(self.path_log_peaks, "a") as f:
            f.write(output_str)

    #   Created: (2020-06-24)-(2252-45)
    def EdgeNotifications(self):
    #   {{{
        func_name = inspect.currentframe().f_code.co_name
        func_printdebug = 1
        flag_notify_edges_time = True
        notify_edges_time_begin = 25
        notify_edges_time_multiple = 10

        #   Initalise edge_status_DIR if None
        if (self.edge_status_DIR == None):
        #   {{{
            loop_i = 0
            self.edge_status_DIR = []
            self.edge_qty_DIR = []

            while (loop_i < len(self.edges_list_DIR)):
                self.edge_status_DIR.append(-1)
                loop_i += 1

            if (func_printdebug == 1):
                sys.stderr.write("%s, initalise edge_status_DIR=(%s)\n" % (func_name, str(self.edge_status_DIR)))
            return
        #   }}}

        #   Loop, rising/falling edges, DIR
        loop_i = 0
        while (loop_i < len(self.edge_status_DIR)):
        #   {{{
            loop_edge_status = self.edge_status_DIR[loop_i]
            loop_edge_qty = self.edges_list_DIR[loop_i]

            #   Rising Edge, DIR
            #   {{{
            if (self.DIR_qty_now > loop_edge_qty):
                if (loop_edge_status == 0):
                    message_str = "Rising Edge, DIR, %s\n" % (str(loop_edge_qty))
                    sys.stderr.write(message_str)
                    self.WriteLogEdges(message_str)
                    if (self.flag_notify_edges_DIR == True and self.flag_notify_rising_edges == True):
                        notification_title = "Falling Edge"
                        notification_subtitle = "DIR"
                        notification_text = "%s" % str(loop_edge_qty)
                        rumps.notification(notification_title, notification_subtitle, notification_text)
                self.edge_status_DIR[loop_i] = 1
            #   }}}

            #   Falling Edge, DIR
            #   {{{
            if (self.DIR_qty_now < loop_edge_qty):
                if (loop_edge_status == 1):
                    message_str = "Falling Edge, DIR, %s\n" % (str(loop_edge_qty))
                    sys.stderr.write(message_str)
                    self.WriteLogEdges(message_str)
                    if (self.flag_notify_edges_DIR == True and self.flag_notifiy_falling_edges == True):
                        notification_title = "Falling Edge"
                        notification_subtitle = "DIR"
                        notification_text = "%s" % str(loop_edge_qty)
                        rumps.notification(notification_title, notification_subtitle, notification_text)
                self.edge_status_DIR[loop_i] = 0
            #   }}}

            loop_i += 1
        #   }}}

    #   }}}

    #   Created: (2020-06-25)-(1734-43)
    def WriteLogEdges(self, message_str):
    #   {{{
        func_name = inspect.currentframe().f_code.co_name
        global self_flag_log
        if (self_flag_log == True):
            datetime_str = datetime.datetime.now(tzlocal()).strftime("%Y-%m-%dT%H:%M:%S%Z")
            epoch_str = str(int(time.time()))
            #epoch_str = str(int(epoch_str))
            path_log = self.path_log_edges
            #f = open(path_log, "w")
            output_str = datetime_str + "\t" + message_str
            with open(path_log, "a") as logfile:
                logfile.write(output_str)
    #   }}}

    #   Function: func_poll()
    #   About: 
    def func_poll(self, sender):
    #   {{{
        func_name = inspect.currentframe().f_code.co_name
        global self_printdebug
        func_printdebug = self_printdebug
        schedule_poll_starttime = time.time()
        #self.
        self.ReadVars_Schedule()

        #flag_deltafile = 1
        deltafile_delta_mins_report_upper = 20
        deltafile_delta_mins_report_lower = 60 * 3 

        self.poll_epoch = datetime.datetime.now().strftime("%s")

        ##   #   Call pulse_delta_file (get the 
        #pulse_deltafile_result = self.pulse_delta_file()
        #pulse_deltafile_epochstart = pulse_deltafile_result[0]
        #pulse_deltafile_epochend = pulse_deltafile_result[1]
        #pulse_deltafile_count = pulse_deltafile_result[2]
        #pulse_deltafile_elapsed = pulse_deltafile_result[3]

        pulse_deltafile_delta_start = 0
        pulse_deltafile_delta_end = 0
        pulse_deltafile_delta_start_dhms = "0"
        pulse_deltafile_delta_end_dhms = "0"
        ##   try block: calculate pulse_deltafile_delta_start
        ##   {{{
        #try:
        #    pulse_deltafile_delta_start = int(self.poll_epoch) - int(pulse_deltafile_epochstart)
        #    pulse_deltafile_delta_start_dhms = self.CmcatUtil_Seconds2DHMS(pulse_deltafile_delta_start)
        #    pulse_deltafile_delta_end = int(self.poll_epoch) - int(pulse_deltafile_epochend)
        #    pulse_deltafile_delta_end_dhms = self.CmcatUtil_Seconds2DHMS(pulse_deltafile_delta_end)
        #except Exception as e:
        #    sys.stderr.write("%s, failed to read pulse_delta_file\n" % str(func_name))
        #    sys.stderr.write("e=(%s)\n" % str(e))
        ##   }}}

        #if (func_printdebug == 1):
        #    sys.stderr.write("pulse_deltafile_delta_start_dhms=(%s)\n" % str(pulse_deltafile_delta_start_dhms))
        #    sys.stderr.write("pulse_deltafile_delta_end_dhms=(%s)\n" % str(pulse_deltafile_delta_end_dhms))
        #    sys.stderr.write("pulse_deltafile_delta_start=(%s)\n" % str(pulse_deltafile_delta_start))
        #    sys.stderr.write("pulse_deltafile_delta_end=(%s)\n" % str(pulse_deltafile_delta_end))

        poll_str = ""
        #   Get DIR/Can scheduleCalc_import values / mtimes
        self.Can_qty_previous = self.Can_qty_now
        self.DIR_qty_previous = self.DIR_qty_now
        try:
            self.DIR_qty_now = self.scheduleCalc.main(self.DIR_args)
            self.Can_qty_now = self.scheduleCalc.main(self.Can_args)
            source_mtime_secs = self.scheduleCalc.GetSourceDeltaMtime()
            source_mtime_dhms = self.scheduleCalc.ScheduleCalc_Seconds2DHMS(source_mtime_secs)
        except Exception as e:
            sys.stderr.write("%s, exception, scheduleCalc: %s, %s\n" % (func_name, str(type(e)), str(e)))

        try:
            date_now = datetime.datetime.now()
            source_time_final_instance_DIR = self.scheduleCalc.TimeOfFinalInstance(str(self.DIR_filter))
            DIR_update_delta_M = (date_now - source_time_final_instance_DIR).total_seconds() / 60 
            DIR_update_delta_M = int(DIR_update_delta_M)
            #source_time_final_instance_Can= self.scheduleCalc.TimeOfFinalInstance(str(self.Can_filter), )
            source_time_final_instance_Can= self.scheduleCalc.TimeOfFinalInstance(str(self.Can_filter))
            Can_update_delta_M = (date_now - source_time_final_instance_Can).total_seconds() / 60 
            Can_update_delta_M = int(Can_update_delta_M)
            d_delta = self.DIR_qty_now - self.DIR_qty_previous
            c_delta = self.Can_qty_now - self.Can_qty_previous
            #   <*>_delta_sign 
            #   {{{
            if (d_delta != 0):
                d_sign = math.copysign(1, d_delta)
                if (d_sign != self.DIR_delta_sign):
                    self.DIR_delta_sign = d_sign
            if (c_delta != 0):
                c_sign = math.copysign(1, c_delta)
                if (c_sign != self.Can_delta_sign):
                    self.Can_delta_sign = c_sign
            #   }}}
            DIR_label_qty = "D" + str(round(self.DIR_qty_now, self._pulse_output_decimals))
            Can_label_qty = "C" + str(round(self.Can_qty_now, self._pulse_output_decimals))
        #   Add Labels: (🔺, 🔻)
        #   {{{
            label_up = "🔺"
            #   Note: (2020-06-16)-(0034-17) Disable downwards label -> set it to ""
            #label_down="🔻"
            label_down = " "
            label_item_delta = "⏳"
            #label_delta_postfix = "⏳"
            label_delta_postfix = ""
            label_delta_prefix = ""

            #   If current loop qty is increasing/decreasing, and the previous qty was doing the opposite, log max/min value
            if (self.DIR_delta_sign_previous < 0 and self.DIR_delta_sign > 0):
                self.WriteLogPeaks("D-IR\tmin\t%s" % str(self.DIR_qty_now))
            if (self.DIR_delta_sign_previous > 0 and self.DIR_delta_sign < 0):
                self.WriteLogPeaks("D-IR\tmax\t%s" % str(self.DIR_qty_now))
            if (self.Can_delta_sign_previous < 0 and self.Can_delta_sign > 0):
                self.WriteLogPeaks("Can\tmin\t%s" % str(self.Can_qty_now))
            if (self.Can_delta_sign_previous > 0 and self.Can_delta_sign < 0):
                self.WriteLogPeaks("Can\tmax\t%s" % str(self.Can_qty_now))

            self.DIR_delta_sign_previous = self.DIR_delta_sign
            self.Can_delta_sign_previous = self.Can_delta_sign

            if (self.DIR_delta_sign > 0):
                DIR_label_qty += label_up
            elif (self.DIR_delta_sign < 0):
                DIR_label_qty += label_down
            if (self.Can_delta_sign > 0):
                Can_label_qty += label_up
            elif (self.Can_delta_sign < 0):
                Can_label_qty += label_down

        #   }}}
            poll_deltas_str = ""
            if (self.flag_DIR_delta == True):
                if (DIR_update_delta_M < self.update_delta_M_max):
                    if (len(poll_deltas_str) > 0):
                        poll_deltas_str += "|"
                    poll_deltas_str += str(DIR_update_delta_M)
            if (self.flag_Can_Delta == True):
                if (Can_update_delta_M < self.update_delta_M_max):
                    if (len(poll_deltas_str) > 0):
                        poll_deltas_str += "|"
                    poll_deltas_str += str(Can_update_delta_M) 
            if (len(poll_deltas_str) > 0):
                poll_deltas_str += label_item_delta
            poll_str += poll_deltas_str
            if (self.DIR_qty_now > self.poll_qty_threshold):
                poll_str += DIR_label_qty
            if (self.Can_qty_now > self.poll_qty_threshold):
                poll_str += Can_label_qty
            poll_str = poll_str.strip()
            #self.app.title = poll_str
            app.title = poll_str
            schedule_poll_endtime = time.time()
            schedule_poll_delta_ns = round(1000 * (schedule_poll_endtime - schedule_poll_starttime), 1)
            report_str = poll_str + " poll_delta=(%s), file_update_delta=(%s)" % (schedule_poll_delta_ns, source_mtime_dhms)
            sys.stderr.write("%s\n" % str(report_str))
            sys.stderr.write("\n")
            #   Call EdgeNotifications()
            self.EdgeNotifications()
            self.poll_count += 1
        except Exception as e:
            sys.stderr.write("%s, %s, Exception while updating label" % (type(e), str(e)))

    #   }}}


#   }}}1


if __name__ == '__main__':
    app = PulseApp()
    app.run()











#   Previous:
#   {{{3
#   Custom Quit Handler Button:
#   Application
#   @rumps.clicked('Clean Quit')
#   def clean_up_before_quit(_):
#       print('execute clean up code')
#       rumps.quit_application()
#   Launcher
#   app = rumps.App('Hallo Thar', menu=['Print Something', 'On/Off Test', 'Quit'], quit_button=None)
    #DIR_args = [ "--printoff", "--now", "--filter", str(DIR_filter), "--onset", str(DIR_onset), "--halflife", str(DIR_HL) ]
    #Can_args = [ "--printoff", "--now", "--filter", str(Can_filter), "--onset", str(Can_onset), "--halflife", str(Can_HL) ]
    #def run(self):
    #   {{{
        #self.EdgeNotifications()
        #self.timer = rumps.Timer(self.func_poll, self.poll_dt)
        #self.timer.start()
        #self.app.run()
    #   }}}
#   }}}1


