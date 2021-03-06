# ppftps

Push Push directories over a secured FTP connection.

For [KeePass] accounts you need to set valid KDBX='/path/to/db.kdbx',
KDBXPW=\"$(cmd_get_kdbx_master_pw)\" and KDBXUUID='server-uuid' vars
in your shell environment or wrapper script.

## Install

```sh
pip install ppftp
pip install pykeepass # for KeePass support
```

and create a ftp wrapper script with your settings in your project directory

```sh
#!/bin/sh

KDBX="${HOME}/.keepass/ftp.kdbx" \
KDBXPW="$(x11-ssh-askpass ftp.kdbx master password)" \
KDBXUUID="KDBX-UUID" \
ppftps $@
```

## Usage

```sh
./ftp push ./local-folder /absolut/path/remote/folder
```

[KeePass]: https://keepass.info "KeePass Password Safe"
