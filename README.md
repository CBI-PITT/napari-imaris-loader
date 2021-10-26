# napari-imaris-loader

[![License](https://img.shields.io/pypi/l/napari-imaris-loader.svg?color=green)](https://github.com/AlanMWatson/napari-imaris-loader/raw/master/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-imaris-loader.svg?color=green)](https://pypi.org/project/napari-imaris-loader)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-imaris-loader.svg?color=green)](https://python.org)
[![tests](https://github.com/AlanMWatson/napari-imaris-loader/workflows/tests/badge.svg)](https://github.com/AlanMWatson/napari-imaris-loader/actions)
[![codecov](https://codecov.io/gh/AlanMWatson/napari-imaris-loader/branch/master/graph/badge.svg)](https://codecov.io/gh/AlanMWatson/napari-imaris-loader)

Napari plugin for loading Bitplane Imaris files '.ims'.  


## Notes:
**For this plugin to work "File/Preferences/Experimental/Render Images Asynchronously" must be selected.**

### Features

* Multiscale Rendering
  * Image pyramids which are present in the native IMS format are automatically added to napari during file loading.
* Chunks are implemented by dask and matched to the chunk sizes stored in each dataset.  (Napari appears to only ask for 2D chunks - unclear how helpful this feature is currently)
* Successfully handles multi-terabyte multi-channel datasets (see unknowns).
* Higher 3D rendering quality is enabled by a widget that reloads data after specifying the lowest resolution level (higher number = lower resolution) to be included in the multiscale series.  Must be done while in 2D rendering mode.

### Known Issues / limitations

* Currently, this is **only an image loader**, and there are no features for loading or viewing objects
* Napari sometimes throws errors indicating that it expected a 3D or 5D array but receives the other.
  * This sometimes *but relatively rarely* causes napari to crash
  * Would like to enable Asynchronous Tiling of Images, but this results in more instability and causes crashes.
* Contrast_Limits are currently determined by dtype and not the actual data.
  * float: [0,1], uint8: [0,254], uint16: [0,65534]
  * Future implementations may use the HistogramMax parameter to determine this.
* 3D rendering works, but it is suggested to turn on 1 channel at a time starting from the highest channel to avoid some OpenGL errors and misalignment errors.
  * For example: Turn on only Channel 1, activate 3D rendering, then turn on Channel 0.

### Unknowns

* Time series data has not been tested, but it has been designed to work.


----------------------------------

This [napari] plugin was generated with [Cookiecutter] using with [@napari]'s [cookiecutter-napari-plugin] template.

<!--
Don't miss the full getting started guide to set up your new package:
https://github.com/napari/cookiecutter-napari-plugin#getting-started

and review the napari docs for plugin developers:
https://napari.org/docs/plugins/index.html
-->

## Installation

You can install `napari-imaris-loader` via [pip]:

    pip install napari-imaris-loader

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [BSD-3] license,
"napari-imaris-loader" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[file an issue]: https://github.com/AlanMWatson/napari-imaris-loader/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
