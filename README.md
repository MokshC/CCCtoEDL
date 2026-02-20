# CCC to EDL

**Usage:**
`CCCtoEDL.py [-h] -e EDL -c CCCDIR [-v] [-l] [-p PATTERN]`

  **Description:**
Converts EDL and CCCs to EDL with CDL values.

## Arguments:

| Flags                             | Description                             | Optional                             |
|------------------------------------|-----------------------------------------|-----------------------------------------|
| `-h`, `--help`                     | Show this help message and exit        | Optional
| `-e EDL`, `--edl EDL`              | Input EDL file                         | **Required**
| `-c CCCDIR`, `--cccdir CCCDIR`    | Directory with CCC files               | **Required**
| `-v`, `--verbose`                  | Give verbose logging                   | Optional (defaults to none)
| `-l`, `--loose`                    | Finds cdl matches loosely              | Optional (defaults to strict)
| `-p PATTERN`, `--pattern PATTERN`  | Specify file extension pattern         | Optional (defaults to .ccc)
