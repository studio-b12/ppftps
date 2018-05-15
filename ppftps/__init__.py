"""
Push Push FTPS
"""
import os
from os import environ as env

import sys

import argparse

import ftplib
import ftputil


__all__ = ["cli", "get_account", "connect", "cmd_push", "cmd_pull", "cmd_ls", "cmd_rm"]

class FTPTLSSession(ftplib.FTP_TLS):

    def __init__(self, host, user, password, port):
        ftplib.FTP_TLS.__init__(self)
        self.connect(host, port)
        self.auth()
        self.login(user, password)
        self.prot_p()
        self.set_pasv(True)

def get_account():
    """Returns an account
        { url: host[:port], username: login, password: password }
    """

    xdb = env.get('KDBX', None)
    xpw = env.get('KDBXPW', None)
    uuid = env.get('KDBXUUID', None)

    if xdb and xpw:
        from pykeepass import PyKeePass
        acc = PyKeePass(xdb, xpw).find_entries(uuid=uuid, first=True)
        if acc:
            return acc
        for acc in PyKeePass(xdb, xpw).entries:
            if acc.url:
                print("UUID=%s URL=%s PATH=%s" % (acc.uuid, acc.url, acc.path))
        raise LookupError("No account. Set a valid KDBXUUID=UUID")

    raise LookupError("set KDBX, KDBXPW and KDBXUUID.")

def connect(acc):
    host, port = acc.url.split(':', 1) if ':' in acc.url else (acc.url, '21')
    port = int(port)
    return ftputil.FTPHost(host,
                           acc.username, acc.password,
                           port=port, session_factory=FTPTLSSession)

def cmd_ls(con, paths):
    for path in paths:
        if con.path.isfile(path):
            path = con.path.dirname(path)
        for entry in con.listdir(path):
            print(con.path.join(path, entry))

def cmd_rm(con, paths):
    for path in paths:
        if con.path.isdir(path):
            con.rmtree(path, ignore_errors=True)
        else:
            con.remove(path)
        print("removed: %s" % path)

def collect(filesystem, src):
    if filesystem.path.isfile(src):
        parent = filesystem.path.dirname(src)
        yield (parent, parent, [filesystem.path.basename(src)])

    for root, _, files in filesystem.walk(src):
        yield (src, root, files)

def entries(sfs, src, dfs, dst, mkdirs=True):
    for base, root, files in collect(sfs, src):
        path = dfs.path.join(dst, (root.split(base, 1)[1]).lstrip('/'))
        if mkdirs:
            try:
                dfs.makedirs(path, exist_ok=True)
            except TypeError:
                dfs.makedirs(path)

        for i in files:
            yield (sfs.path.join(root, i), dfs.path.join(path, i))

def _do(cmd, sfs, src, dfs, dst, forced=False):
    def _exc(cmd, files, forced=False):
        for spath, dpath in files:
            try:
                cmd(spath, dpath, forced)
            except Exception:
                try:
                    dfs.remove(dpath)
                except Exception:
                    pass
                yield (spath, dpath)

    yield from _exc(cmd, _exc(cmd, entries(sfs, src, dfs, dst), forced), True)

def cmd_push(con, src, dst, forced=False):
    def _push(spath, dpath, forced=False):
        if forced:
            con.upload(spath, dpath)
        elif not con.upload_if_newer(spath, dpath):
            return
        print("pushed: %s (forced=%r)" % (dpath, forced))

    for spath, dpath in _do(_push, os, src, con, dst, forced):
        print("push error: %s -> %s" % (spath, dpath), file=sys.stderr)

def cmd_pull(con, src, dst, forced=False):
    def _pull(spath, dpath, forced=False):
        if forced:
            con.download(spath, dpath)
        elif not con.download_if_newer(spath, dpath):
            return
        print("pulled: %s (forced=%r)" % (spath, forced))

    for spath, dpath in _do(_pull, con, src, os, dst, forced):
        print("pull error: %s -> %s" % (spath, dpath), file=sys.stderr)

def cli(account=get_account):
    parser = argparse.ArgumentParser(
        description="""Push Push directories over a secured FTP connection.""",
        epilog="""For KeePass accounts you to set valid KDBX='/path/to/db.kdbx',
        KDBXPW=\"$(cmd_get_kdbx_master_pw)\" and KDBXUUID='server-uuid' vars
        in your environment.
        """)
    parser.add_argument("-f", "--force", action='store_true', help="force operation")

    cmds = parser.add_subparsers(title="commands", dest='which')

    cmdp = cmds.add_parser("pull", help="download directory or file")
    cmdp.add_argument("remote", help="remote path")
    cmdp.add_argument("local", help="local path")

    cmdp = cmds.add_parser("push", help="upload directory or file")
    cmdp.add_argument("local", help="local path")
    cmdp.add_argument("remote", help="remote path")

    cmdp = cmds.add_parser("ls", help="directory listing")
    cmdp.add_argument("path", nargs='+', help="paths to list")

    cmdp = cmds.add_parser("rm", help="delte directory or file")
    cmdp.add_argument("path", nargs='+', help="paths to delete")

    args = parser.parse_args()
    if not args.which:
        parser.print_help()
        sys.exit(1)

    acc = account()
    with connect(acc) as con:
        cmd = args.which
        if cmd == "push":
            cmd_push(con, args.local, args.remote, args.force)
        elif cmd == "pull":
            cmd_pull(con, args.remote, args.local, args.force)
        elif cmd == "ls":
            cmd_ls(con, args.path)
        elif cmd == "rm":
            cmd_rm(con, args.path)
