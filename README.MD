# Sync

Using rsync to sync illumina Sequence run data, ignore some images

## Usage
```shell
python sync.py path/to/chip/base/ 172.17.0.101::backup --port 875 

```
or if you want to pass extra args
```shell
python sync.py path/to/chip/base/ 172.17.0.101::backup --port 875  --extra-args "'--progress --password-file=/path/to/passwd'"

```

```text
usage: sync [-h] [--port PORT] [--extra-args EXTRA_ARGS] [--timeout TIMEOUT]
            [--make-cache] [-v]
            base_dir remote_path

positional arguments:
  base_dir              Base dir of chip run data
  remote_path           Remote path which should be a valid rsync dst
                        expression string

optional arguments:
  -h, --help            show this help message and exit
  --port PORT           rsync port
  --extra-args EXTRA_ARGS
                        extra rsync args to pass
  --timeout TIMEOUT     rsync command timeout
  --make-cache          make cache for all exists chip data and exit
  -v, --verbose         set log level to debug

```
