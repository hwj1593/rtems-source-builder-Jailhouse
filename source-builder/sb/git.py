#
# RTEMS Tools Project (http://www.rtems.org/)
# Copyright 2010-2013 Chris Johns (chrisj@rtems.org)
# All rights reserved.
#
# This file is part of the RTEMS Tools package in 'rtems-tools'.
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

#
# Provide some basic access to the git command.
#

import os

import defaults
import error
import execute
import path

class repo:
    """An object to manage a git repo."""

    def _git_exit_code(self, ec):
        if ec:
            raise error.general('git command failed (%s): %d' % (self.git, ec))

    def _run(self, args, check = False):
        e = execute.capture_execution()
        exit_code, proc, output = e.spawn([self.git] + args)
        if check:
            self._git_exit_code(exit_code)
        return exit_code, output

    def __init__(self, _path, _opts, _defaults):
        self.path = _path
        self.opts = _opts
        self.default = _defaults
        self.git = _opts.expand('%{__git}', _defaults)

    def git_version(self):
        ec, output = self._run(['--version'], True)
        gvs = output.split()
        if len(gvs) < 3:
            raise error.general('invalid version string from git: %s' % (output))
        vs = gvs[2].split('.')
        if len(vs) != 4:
            raise error.general('invalid version number from git: %s' % (gvs[2]))
        return (int(vs[0]), int(vs[1]), int(vs[2]), int(vs[3]))

    def status(self):
        _status = {}
        ec, output = self._run(['status'])
        if ec == 0:
            state = 'none'
            for l in output.split('\n'):
                if l.startswith('# On branch '):
                    _status['branch'] = l[len('# On branch '):]
                elif l.startswith('# Changes to be committed:'):
                    state = 'staged'
                elif l.startswith('# Changes not staged for commit:'):
                    state = 'unstaged'
                elif l.startswith('# Untracked files:'):
                    state = 'untracked'
                elif state != 'none' and l[0] == '#':
                    if l.strip() != '#' and not l.startswith('#   ('):
                        if state not in _status:
                            _status[state] = []
                        l = l[1:]
                        if ':' in l:
                            l = l.split(':')[1]
                        _status[state] += [l.strip()]
        return _status

    def clean(self):
        _status = self.status()
        return len(_status) == 1 and 'branch' in _status

    def valid(self):
        ec, output = self._run(['status'])
        return ec == 0

    def remotes(self):
        _remotes = {}
        ec, output = self._run(['config', '--list'])
        if ec == 0:
            for l in output.split('\n'):
                if l.startswith('remote'):
                    ls = l.split('=')
                    if len(ls) >= 2:
                        rs = ls[0].split('.')
                        if len(rs) == 3:
                            r_name = rs[1]
                            r_type = rs[2]
                            if r_name not in _remotes:
                                _remotes[r_name] = {}
                            if r_type not in _remotes[r_name]:
                                _remotes[r_name][r_type] = []
                            _remotes[r_name][r_type] = '='.join(ls[1:])
        return _remotes

    def head(self):
        hash = ''
        ec, output = self._run(['log', '-n', '1'])
        if ec == 0:
            l1 = output.split('\n')[0]
            if l1.startswith('commit '):
                hash = l1[len('commit '):]
        return hash

if __name__ == '__main__':
    import sys
    _opts, _defaults = defaults.load(sys.argv)
    g = repo('.', _opts, _defaults)
    print g.git_version()
    print g.valid()
    print g.status()
    print g.clean()
    print g.remotes()
    print g.head()