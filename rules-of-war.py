#! /usr/bin/env python

import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),"code"))

from core import shell

S = shell.Shell(*sys.argv)
S.run()


