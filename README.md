# [Unformat](https://github.com/johnmcfarlane/unformat)

Python3 utility to generate a *.clang-format* file from example code-base.

## Description

Given the path to a C, C++ or Objective-C project, attempts to generate the perfect *.clang-format* file. 
It does this by producing configuration files with random variations and measuring how much code they would change. 
Finally the configuration file with the least change is output.

## Dependencies

Tested under Python 3.5 using *clang-format 3.9* and *clang-format 3.8*.

Python modules you'll need to install:

* [PyYAML](http://pyyaml.org/)
* [python-Levenshtein](https://pypi.python.org/pypi/python-Levenshtein)

To add dependencies to a Ubuntu or Debian system:

```sh
sudo apt install clang-format python3-levenshtein python3-yaml
```

## Examples

If Unformat is cloned into */home/abc/unformat* and C++ source code is in */home/abc/my_project*,

```sh
python3 /home/abc/unformat --root /home/abc/my_project /home/abc/my_project/**/*.h /home/abc/my_project/**/*.cpp
```

will search for the best *.clang-format* file. 
It will start searching from */home/abc/my_project/.clang-format*
and will write new configurations to that location as they are found.
(Note you must have 
[globstar enabled](http://shellrunner.com/better-simpler-searching-and-scripting-with-bash-globstar/)
to make use of recursive (`**`) wildcards.)

The search may continue indefinitely.
Press Ctrl-C to stop early. 
Any intermediate results will be written out.

## Links

To submit feedback and bug reports, please file an [issue](https://github.com/johnmcfarlane/unformat/issues).  
For another solution to this problem, check out [whatstyle](https://github.com/mikr/whatstyle).
