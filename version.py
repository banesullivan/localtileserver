"""Version info for flask-tileserver.

On the default branch, use 'dev0' to denote a development version.
For example:

    version_info = 0, 2, 'dev0'

---

When generating pre-release wheels, use '0rcN', for example:

    version_info = 0, 2, '0rc1'

Which denotes the first release candidate.

"""
# major, minor, patch
version_info = 0, 0, 2

# Nice string for the version
__version__ = ".".join(map(str, version_info))
