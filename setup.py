#   VIM SETTINGS: {{{3
#   VIM: let g:mldvp_filecmd_open_tagbar=0 g:mldvp_filecmd_NavHeadings="" g:mldvp_filecmd_NavSubHeadings="" g:mldvp_filecmd_NavDTS=0 g:mldvp_filecmd_vimgpgSave_gotoRecent=0
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=3: 
#   }}}1
from setuptools import setup
import pkg_resources
import re
import pulse

#   Bug with py2app/pyinstaller/setuptools, or, the reason this thing didn't work the first time.
#   {{{2
#       Previous:
#       {{{
#       LINK: https://github.com/pypa/setuptools/issues/1963
#       Resolution: Use older version of setuptools:
#       pip3 install --upgrade 'setuptools<45.0.0'
#       Until they fix this, the app can be run from the .py script file
#       }}}
#       Update: (2020-06-13)-(1641-10)
#       {{{
#       Install wxPython:
#           #>>     pip3 install -U wxPython
#       Build with:
#           --packages=wx
#       }}}
#   }}}1


version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('pulse/__main__.py').read(),
    re.M
    ).group(1)


#APP = ['pulse.py']
#APP = [ 'pulse/__main__.py'  ]
APP = [ 'main.py'  ]
packages = ['rumps', 'pulse', 'dtscan', 'pandas', 'dateparser' ]

DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon-pulse.icns',
    'plist': {
        'CFBundleShortVersionString': '0.1',
        'LSUIElement': True,
    },
    'packages': packages,
    'includes': packages,
    'argv_emulation': True,
}

setup(
    app=APP,
    name="Pulse",
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=packages, 
    install_requires=packages
)


#    'PyRuntimeLocations': [
#     '@executable_path/../Frameworks/libpython3.4m.dylib',
#     '/Applications/anaconda/lib/libpython3.4m.dylib'
#    ]

