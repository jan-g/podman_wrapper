import json
import logging
import os
import pathlib
import sys


LOG = logging.getLogger(__name__)


def config():
    try:
        with open(pathlib.Path.home() / ".docker-shim") as f:
            cfg = json.load(f)
        return cfg
    except:
        cfg = {"mode": "echo", "docker": "/usr/local/bin/docker", "podman": "podman"}
        LOG.warning("initialising docker-shim to echo commands")
        write_config(cfg)
        return cfg


def write_config(cfg):
    with open(pathlib.Path.home() / ".docker-shim", "w") as f:
        json.dump(cfg, f)


def main():
    cfg = config()
    argv = sys.argv[1:]

    if len(argv) == 2 and argv[0] == "use":
        mode = cfg["mode"] = argv[1]
        LOG.info(f"updating docker-shim to use {mode}")
        write_config(cfg)
        return

    if cfg["mode"] == "echo":
        print("docker", *argv, file=sys.stderr)
        sys.exit(1)

    elif cfg["mode"] == "docker":
        docker = cfg["docker"]
        os.execvp(docker, [docker, *argv])

    elif cfg["mode"] != "podman":
        LOG.error("can only support echo, docker, or podman")
        sys.exit(1)

    home = str(pathlib.Path.home())

    # Handle subcommands
    if argv[0] in ("create", "run"):
        i = 0
        while i < len(argv):
            if argv[i] == "-v":
                i += 1
                if argv[i].startswith(home):
                    argv[i] = "/mnt" + argv[i][len(home):]
            i += 1

    elif argv[0] in ("start", ):
        # `docker start -i ...` looks to behave like `podman start -a -i ...`
        if "-i" in argv:
            argv = [argv[0], "-a", *argv[1:]]

    with open("/dev/tty", "w") as f:
        print(f"executing {argv}", file=f)

    podman = cfg["podman"]
    os.execvp(podman, [podman, *argv])


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()

