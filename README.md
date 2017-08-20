# [Unformat](https://github.com/johnmcfarlane/unformat)

Python3 utility to generate a *.clang-format* file from example code-base.

## Description

Given the path to a C, C++ or Objective-C project, attempts to generate the perfect *.clang-format* file. 
It does this by producing configuration files with random variations and measuring how much code they would change. 
Finally the configuration file with the least change is output.

## Dependencies

Tested using *clang-format 3.9*.

Python modules you'll need to install:

* [PyYAML](http://pyyaml.org/)
* [python-Levenshtein](https://pypi.python.org/pypi/python-Levenshtein)

To add dependencies to a Ubuntu or Debian system:

```sh
sudo apt install clang-format-3.9 python3-levenshtein python3-yaml
```

## Examples

If Unformat is clone into in */home/abc/unformat* and C++ source code is in */home/abc/my_project*,

```sh
python3 /home/abc/unformat --root /home/abc/my_project "/home/abc/my_project/**/*.h" "/home/abc/my_project/**/*.cpp"
```

will search for the best *.clang-format* file. 
It will start searching from */home/abc/my_project/.clang-format*
and will write new configurations to that location as they are found.

The search may continue indefinitely.
Press Ctrl-C to stop early. 
Any intermediate results will be written out.