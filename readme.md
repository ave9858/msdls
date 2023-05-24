Microsoft Software Download Listing Script
==========================================
Microsoft Software Download Listing Script checks all the products in a specified range and outputs results into a JSON file compatible with [msdl](https://github.com/ave9858/msdl).

Usage
-----
```
usage: msdls.py [-h] --first FIRST --last LAST [--write WRITE] [--update UPDATE]

Checks which product IDs of the Microsoft Software Download are available.

options:
  -h, --help       show this help message and exit
  --first FIRST    first product ID to check
  --last LAST      last product ID to check
  --write WRITE    save results to the specified JSON file
  --update UPDATE  update the specified JSON with results
```

License
-------
This project is licensed under the terms of GNU Affero General Public License Version 3.
