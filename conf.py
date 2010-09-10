'''
This file is part of PypMsg.

PypMsg is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PypMsg is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with PypMsg.  If not, see <http://www.gnu.org/licenses/>.
'''

import os
from uuid import uuid4 as get_uuid
from pickle import HIGHEST_PROTOCOL as PK_PROTOCOL
import ConfigParser as cp


USERNAME = os.environ.has_key('USER') and os.environ['USER'] or 'pm_user'
HOMEDIR = os.environ.has_key('HOME') and os.environ['HOME'] or '.'

HOST = ''
EXIT_HOST = 'localhost'
PORT = 50007
BROADCAST = '<broadcast>'

BULK_FILEDATA = 2048
BULK_METADATA = 4096

FILSEP = chr(28) #FS

ACK = 'ACK'

SYSTEM_DEFAULTS = {
        'home-dir': os.environ.has_key('HOME') and os.environ['HOME'] or '.',
        'host': '',
        'exit-host': 'localhost',
        'port': '50007',
        'broadcast': '<broadcast>',
        'bulk-filedata': '2048',
        'bulk-metadata': '4096'
}

USER_DEFAULTS = {
        'user-name': os.environ.has_key('USER') and os.environ['USER'] or 'pm_user'
}

SETTINGS_FILE = 'prefs.cfg'
sysSection = 'PM-system'
userSection = 'PM-user'

if not os.path.exists(SETTINGS_FILE):
    tempConf = cp.ConfigParser()
    tempConf.add_section(sysSection)
    for key, val in SYSTEM_DEFAULTS.items():
        tempConf.set(sysSection, key, val)
    tempConf.add_section(userSection)
    for key, val in USER_DEFAULTS.items():
        tempConf.set(userSection, key, val)
    tempConf.write(open(SETTINGS_FILE, 'w'))

prefs = cp.ConfigParser()
prefs.read(SETTINGS_FILE)
