# SketchSeed

#### Video Demo: <https://youtu.be/Ae13EAd6cV4>

## Overview

**SketchSeed** is a Python command-line tool that generates Arduino C++ starter code for ESP32 projects from a JSON configuration file.

It validates component names, GPIO assignments, and supported hardware constraints before generating a `.ino` sketch and a `pins.h` header file.

### Features

- Generate Arduino starter code from a JSON configuration.
- Validate GPIO assignments and detect conflicting pin usage.
- Check component names and supported component types.
- Catch common configuration errors before generating code.
- Write generated files to a user-specified output directory.
- Run automated tests with `pytest`.

## Motivation

I built SketchSeed as my CS50P final project to address a repetitive task when starting microcontroller projects. I often spend the first 15 to 30 minutes writing similar boilerplate C++ code in the Arduino IDE: defining pin constants, configuring `pinMode()` settings in `setup()`, setting up input pull-up resistors for buttons, and writing basic input/output logic in `loop()`.

Small configuration mistakes can also cause problems during development. Examples include assigning a component to an unsuitable GPIO pin, assigning the same pin to multiple components, or using a name that is not a valid identifier. SketchSeed checks supported configuration rules in Python before generating the starter code, helping identify common mistakes earlier in the workflow.

## Installation and Requirements

SketchSeed uses Python's standard library at runtime, so no third-party packages are required to run `project.py`.

To run the automated tests, install `pytest`:

```bash
python -m pip install pytest
```

## How to Run SketchSeed

Generate code from the example configuration:

```bash
python project.py examples/smart_led.json --out build/smart_led
```

This creates the generated files in `build/smart_led/`:

- `pins.h`
- `smart_led.ino`

Open the generated files in the Arduino IDE and review them for your target board before compiling or uploading them.

To run the test suite:

```bash
python -m pytest -v
```

## Example Configuration

The `examples/smart_led.json` file provides a sample configuration for a simple ESP32 project with a push button on GPIO 4 and a status LED on GPIO 5. Use it as a starting point when creating your own project configurations.

## File Structure and Code Overview

### 1. `project.py`

This is the main program and contains the code-generation pipeline. Its main functions are:

- **`load_config(path)`**: Reads and parses a JSON configuration file. It handles a missing file and malformed JSON with clear errors, and checks that the parsed JSON root is a dictionary.
- **`validate_config(config)`**: Checks the configuration against the rules implemented in SketchSeed. These include supported boards and component types, identifier syntax, duplicate component names, GPIO conflicts, and applicable pin restrictions. Constants such as `SUPPORTED_BOARDS`, `SUPPORTED_TYPES`, `ESP32_MIN_PIN`, `ESP32_MAX_PIN`, and `ESP32_INPUT_ONLY_PINS` keep these rules in one place. The code uses `type(pin) is not int` to reject Boolean values, since Python treats `bool` as a subclass of `int`.
- **`generate_sketch(config)`**: Converts a validated configuration into C++ source text. It generates a `pins.h` header with header guards and named pin constants, along with an `.ino` sketch containing setup code and starter logic for the configured components.
- **`write_project(files, out_dir)`**: Creates the output directory when needed and writes the generated files using UTF-8 encoding.
- **`main()`**: Parses command-line arguments with `argparse`, runs the pipeline, and returns an appropriate process exit status for success or failure.

### 2. `test_project.py`

This file contains the automated tests written with `pytest`. The tests cover the main functions and common edge cases, including missing files, malformed JSON, unsupported boards, invalid identifiers, GPIO conflicts, Boolean pin values, pin restrictions, and file creation. The `tmp_path` fixture allows tests to use temporary files and directories without cluttering the project folder.

### 3. `requirements.txt`

SketchSeed has no third-party runtime dependencies. The `requirements.txt` file lists `pytest`, which is needed to run the test suite.

### 4. `examples/smart_led.json`

This example configuration demonstrates how to describe a simple project in JSON. It defines a push button and a status LED using GPIO 4 and GPIO 5.

## Design Choices and Trade-offs

### Standard library instead of a templating library

I considered using a templating engine such as Jinja2 to generate the C++ source code. I chose Python's built-in string handling instead, keeping SketchSeed lightweight and avoiding third-party runtime dependencies.

### Standalone functions instead of a class

I considered creating a `SketchBuilder` class, but chose a pipeline of standalone functions: load, validate, generate, and write. This keeps the stages separate and makes them easier to test independently.

### Validate configuration before generating code

SketchSeed checks configuration rules in Python before writing the output files. This allows it to report supported configuration errors early, rather than leaving every issue to be discovered during compilation or hardware testing.

## Limitations

SketchSeed is intentionally limited in scope. It supports only the boards and component types implemented in the current version. Its validation checks cannot guarantee that a physical circuit is wired correctly or that generated code will compile and behave as intended on every board configuration. Review the generated code and verify the target board's pin capabilities before compiling and testing it with hardware.

## Testing

Run the test suite with:

```bash
python -m pytest -v
```

The tests exercise the configuration-loading, validation, generation, and file-writing functions, including common invalid inputs and error cases.

## Video Demonstration

Replace the video-demo placeholder at the top of this README with the YouTube URL for the final demonstration before submitting the project.
