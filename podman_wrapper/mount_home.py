"""
The idea here is that we inject a tunnel into a podman machine and use sshfs to mount our home directory

We simply use this, which works with brew's standard podman machine:

ssh
  -i {the ssh key} -p {the machine port}
  -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no
  -A
  -R 2222:localhost:22
  -t
  {the podman user@host}
  "sudo sshfs {your username}@localhost: /mnt -p 2222 -o uid=1000 -o gid=1000 -o allow_other ; sleep 99d"
"""

import getpass
import os
import pathlib
import random
import urllib.parse

import toml


def main():
    config = pathlib.Path.home() / ".config"
    if "XDG_CONFIG_HOME" in os.environ:
        config = pathlib.Path(os.environ["XDG_CONFIG_HOME"])

    # Strictly this
    with open(config / "containers" / "containers.conf") as f:
        cfg = toml.load(f)

    service = cfg["engine"]["active_service"]
    dest = cfg["engine"]["service_destinations"][service]

    identity = dest["identity"]

    # This is of the format ssh://core@localhost:59684/run/user/1000/podman/podman.sock
    uri = urllib.parse.urlparse(dest["uri"])

    user_host, port = uri.netloc.split(":")

    # Work out who we call back as
    local_user = getpass.getuser()

    randport = random.randrange(2000, 10000)

    os.execvp("ssh", [
        "ssh",
            "-i", identity,
            "-p", port,
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "StrictHostKeyChecking=no",
            "-A",   # because you never know, this might obviate the need for a password prompt
            "-t",   # in case we need to prompt for the local password anyway
            "-R", f"{randport}:localhost:22",
            user_host,
            f"sudo sshfs {local_user}@localhost: /mnt -p {randport} -o uid=1000 -o gid=1000 -o allow_other -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no; sleep 99d"
    ])
