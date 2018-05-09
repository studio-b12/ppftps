import argparse
import ftplib
import ftputil
import os
import sys

from os import environ as env

__all__ = ["cli", "get_account", "connect", "push", "pull", "ls", "rm"]

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

    db = env.get('KDBX', None)
    pw = env.get('KDBXPW', None)
    uuid = env.get('KDBXUUID', None)

    if db and pw:
        from pykeepass import PyKeePass
        a = PyKeePass(db, pw).find_entries(uuid=uuid, first=True)
        if a:
            return a
        for a in PyKeePass(db, pw).entries:
            if a.url:
                print("UUID=%s URL=%s PATH=%s" % (a.uuid, a.url, a.path))
        raise LookupError("No account. Set a valid KDBXUUID=UUID")

    raise LookupError("set KDBX, KDBXPW and KDBXUUID.")

def connect(a):
    host, port = a.url.split(':', 1) if ':' in a.url else (a.url, '21')
    port = int(port)
    return ftputil.FTPHost(host
        , a.username
        , a.password
        , port=port
        , session_factory=FTPTLSSession)

def ls(c, paths):
    for path in paths:
        if c.path.isfile(path):
            path = c.path.dirname(path)
        for entry in c.listdir(path):
            print(c.path.join(path, entry))

def rm(c, paths):
    for path in paths:
        if c.path.isdir(path):
            c.rmtree(path, ignore_errors=True)
        else:
            c.remove(path)
        print("removed: %s" % path)

def collect(fs, src):
    if fs.path.isfile(src):
        s = fs.path.dirname(src)
        yield (s, s, [fs.path.basename(src)])

    for root, _, files in fs.walk(src):
        yield (src, root, files)

    raise StopIteration()

def entries(sfs, src, dfs, dst, mkdirs=True):
    for base, root, files in collect(sfs, src):
        p = dfs.path.join(dst, (root.split(base, 1)[1]).lstrip('/'))
        if mkdirs:
            try:
                dfs.makedirs(p, exist_ok=True)
            except TypeError:
                dfs.makedirs(p)

        for f in files:
            yield (sfs.path.join(root, f), dfs.path.join(p, f))

def _do(op, sfs, src, dfs, dst, forced=False):
    def _exc(op, entries, forced=False):
        for sp, dp in entries:
            try:
                op(sp, dp, forced)
            except Exception as e:
                try:
                    dfs.remove(dp)
                except Exception:
                    pass
                yield (sp, dp)

    yield from _exc(op, _exc(op, entries(sfs, src, dfs, dst), forced), True)

def push(c, src, dst, forced=False):
    def _push(sp, dp, forced=False):
        if forced:
            c.upload(sp, dp)
        elif not c.upload_if_newer(sp, dp):
            return
        print("pushed: %s (forced=%r)" % (dp, forced))

    for sp, dp in _do(_push, os, src, c, dst, forced):
        print("push error: %s -> %s" % (sp, dp), file=sys.stderr)

def pull(c, src, dst, forced=False):
    def _pull(sp, dp, forced=False):
        if forced:
            c.download(sp, dp)
        elif not c.download_if_newer(sp, dp):
            return
        print("pulled: %s (forced=%r)" % (sp, forced))

    for sp, dp in _do(_pull, c, src, os, dst, forced):
        print("pull error: %s -> %s" % (sp, dp), file=sys.stderr)

def cli(get_account=get_account):
    parser = argparse.ArgumentParser(
        description="""Push and pull directories over a secured FTP connection."""
        ,epilog="""For KeyPass accounts you need valid KDBX='/path/to/db.kdbx',
        KDBXPW=\"$(cmd_get_kdbx_master_pw)\" and KDBXUUID='server-uuid'
        vars in your environment.
        """)
    parser.add_argument("-f", "--force", action='store_true', help="force operation")

    cmds = parser.add_subparsers(title="commands", dest='which')

    sp = cmds.add_parser("pull", help="download directory or file")
    sp.add_argument("remote", help="remote path")
    sp.add_argument("local", help="local path")

    sp = cmds.add_parser("push", help="upload directory or file")
    sp.add_argument("local", help="local path")
    sp.add_argument("remote", help="remote path")

    sp = cmds.add_parser("ls", help="directory listing")
    sp.add_argument("path", nargs='+', help="paths to list")

    sp = cmds.add_parser("rm", help="delte directory or file")
    sp.add_argument("path", nargs='+', help="paths to delete")

    args = parser.parse_args()
    if not args.which:
        parser.print_help()
        sys.exit(1)

    a = get_account()
    with connect(a) as c:
        cmd=args.which
        if cmd == "push":
            push(c, args.local, args.remote, args.force)
        elif cmd == "pull":
            pull(c, args.remote, args.local, args.force)
        elif cmd == "ls":
            ls(c, args.path)
        elif cmd == "rm":
            rm(c, args.path)

