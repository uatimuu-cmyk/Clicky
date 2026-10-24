# Clicky

<p align="center">
  <img src="assets/clicky.png" width="180" alt="Clicky logo">
</p>

A simple autoclicker built with Python and PySide6.

## Features

- Configurable mouse clicking
- Keyboard controls
- Graphical interface
- Windows executable builds

## Download

Windows builds are available from [GitHub Actions](https://github.com/uatimuu-cmyk/Clicky/actions).

1. Open a successful build.
2. Download the `Clicky-Windows` artifact.
3. Extract the ZIP file.
4. Run `Clicky.exe`.

## Run from source

Install Python and the required dependencies:

```bash
python -m pip install PySide6 pynput
```

Run the application:

```bash
python autoclicker.py
```

## Build

Windows builds are handled by GitHub Actions using the workflow in `.github/workflows/build-windows.yml`.

Push a commit to `master` to trigger a build.

## Dependencies

- [Python](https://www.python.org/)
- [PySide6](https://doc.qt.io/qtforpython/)
- [pynput](https://pynput.readthedocs.io/)
- [PyInstaller](https://pyinstaller.org/)

