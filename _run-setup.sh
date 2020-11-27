#!/usr/bin/env zsh
#	VIM SETTINGS: {{{3
#	VIM: let g:mldvp_filecmd_open_tagbar=0 g:mldvp_filecmd_NavHeadings="" g:mldvp_filecmd_NavSubHeadings="" g:mldvp_filecmd_NavDTS=0 g:mldvp_filecmd_vimgpgSave_gotoRecent=0
#	vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#	vim: set foldlevel=2 foldcolumn=3: 
#	}}}1
source "$HOME/._exports.sh"
source "$HOME/._bins.sh"
self_name="mld_pulse_run_setup"
#	{{{2

#set -o errexit   # abort on nonzero exitstatus
#set -o nounset   # abort on unbound variable
#set -o pipefail  # don't hide errors within pipes

_pulse_dir="$mld_src/pulse"
_bin_python_build="$HOME/.pyenv/shims/python3"
_pulse_setup="setup.py"
_pulse_flag_output_build_log=0
_pulse_flag_delete_dir_tmp=0

#	Created: (2020-09-27)-(2149-03), containing existing script contents
_Z_run_setup() {
	#	func_name: {z,sh}
	#	{{{
	local func_name=""
	if [[ -n "$ZSH_VERSION" ]]; then 
		func_name=$funcstack[1]
	elif [[ -n "$BASH_VERSION" ]]; then
		func_name="${FUNCNAME[0]}"
	else
		echoerr "$self_qindex, warning, non zsh/bash shell, unable to find func_name"
	fi
	#	}}}
	local func_printdebug=1
	#	func_help: {z,sh}
	#	{{{
	local func_about=""
	local func_help="""$func_name, $func_about
"""
	#if [[ "$1" =~ "^\\s*-h|--help\\s*$" ]]; then
	if echo "${1:-}" | perl -wne '/^\s*-h|--help\s*$/ or exit 1'; then
		echo "$func_help"
		return 2
	fi
	#	}}}

	#	include '--debug-skip-macholib', required if using pyenv version of python, since py2app interpretus that as system-python and defaults to --semi-standalone mode
	#local _cmd_build=( $_bin_python_build "$_pulse_setup"  py2app  --packages=wx  )
	local _cmd_build=( $_bin_python_build "$_pulse_setup"  py2app  )

	local flag_copybuild2Applications=1

	local pulse_dir_tmp="/tmp/Pulse.build."$( date +%s )

	local pulse_path_applications="/Applications/Pulse.app"
	local pulse_path_appbundle="$pulse_dir_tmp/dist/Pulse.app"

	#	Delete pulse_dir_tmp if it exists
	if [[ -e "$pulse_dir_tmp" ]]; then
		echoerr "$func_name, Delete pulse_dir_tmp$nl$tab$pulse_dir_tmp"
		rm -r "$pulse_dir_tmp"
	fi

	cp -r "$_pulse_dir" "$pulse_dir_tmp"
	local previous_path="$PWD"
	cd "$pulse_dir_tmp"

	path_build_log="$pulse_dir_tmp/build-$(date +%s).log"
	echoerr "$func_name, build log:$nl$tab$path_build_log"

	echoerr "$func_name, run setup py2app$nl$tab${_cmd_build[@]}"
	echoerr "$func_name, path_build_log$nl$tab$path_build_log"

	if [[ "$_pulse_flag_output_build_log" -eq 1 ]]; then
		time ( ${_cmd_build[@]}  2&>1 | tee "$path_build_log" )
	else
		time ( ${_cmd_build[@]}  2&>1 | tee "$path_build_log" > /dev/null )
	fi
	echo ""

	if [[ ! -e "$pulse_path_appbundle" ]]; then
		echo "error, not found, pulse_path_appbundle$nl$tab$pulse_path_appbundle"
		echo "check install log$nl$tab$path_build_log"
		return 2
	fi

	#	Quit Pulse if it is running 
	osascript -e 'quit app "Pulse"'

	if [[ "$flag_copybuild2Applications" -eq 1 ]]; then
		if [[ -e "$pulse_path_applications" ]]; then
			echoerr "$func_name, delete$nl$tab$pulse_path_applications"
			rm -r "$pulse_path_applications"
		fi
		echoerr "$func_name, Copy, from->to:$nl$tab$pulse_path_appbundle$nl$tab$pulse_path_applications"
		cp -r "$pulse_path_appbundle" "$pulse_path_applications"
	fi

	echoerr "$func_name, sleep 1"
	sleep 1

	echoerr "$func_name, open pulse:$nl$tab$pulse_path_applications"
	open -a "$pulse_path_applications"

	if [[ "$_pulse_flag_delete_dir_tmp" -eq 1 ]]; then
		echoerr "$func_name, delete pulse_dir_tmp$nl$tab$pulse_dir_tmp"
		rm -r "$pulse_dir_tmp"
	fi
	cd "$previous_path"
}
#	}}}

_Z_run_setup "$@"

#	TODO: (2020-06-25)-(1855-08) qindex_cmcat_python_pulse_run_setup, applescript to enable notifications from pulse: "osascript -e 'tell application "System Events" to make login item at end with properties {path:"/Applications/Pulse.app", hidden:false}'"

#	}}}1

