import argparse
import json
from pathlib import Path
import re
import sys
# Hardware definitions for ESP32
SUPPORTED_BOARDS = {"esp32"}
SUPPORTED_TYPES = {"led", "button"}
ESP32_MIN_PIN = 0
ESP32_MAX_PIN = 39
ESP32_INPUT_ONLY_PINS = {34, 35, 36, 37, 38, 39}

# Valid C variable identifier regex
NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def load_config(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        if not isinstance(data, dict):
            print(f"Error: JSON '{path}' must be a root object.")
            return None
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading configuration '{path}': {e}")
        return None

def validate_config(config):
    """Validates configuration against ESP32 limits and C naming rules."""
    if not config or not isinstance(config, dict):
        raise ValueError("Invalid or empty config data.")

    # 1. Validate Board
    board = config.get("board")
    if board not in SUPPORTED_BOARDS:
        raise ValueError(f"Unsupported board '{board}'. Allowed: {', '.join(SUPPORTED_BOARDS)}")

    # 2. Validate Project Name
    project_name = config.get("project_name")
    if not isinstance(project_name, str) or not NAME_PATTERN.fullmatch(project_name):
        raise ValueError(f"Invalid project name: '{project_name}'")

    # 3. Validate Components Base Array
    components = config.get("components")
    if not isinstance(components, list) or not components:
        raise ValueError("The 'components' field must be a non-empty list.")

    seen_names = set()
    seen_pins = {}

    # 4. Validate Individual Components
    for index, item in enumerate(components):
        prefix = f"Component #{index + 1}"
        if not isinstance(item, dict):
            raise ValueError(f"{prefix} must be a valid JSON object.")

        name = item.get("name")
        comp_type = item.get("type")
        pin = item.get("pin")

        # Check Name rules
        if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
            raise ValueError(f"{prefix} name '{name}' is not a valid C variable name.")
        
        if name in seen_names:
            raise ValueError(f"Duplicate component name found: '{name}'")
        seen_names.add(name)

        # Check Type rules
        if comp_type not in SUPPORTED_TYPES:
            raise ValueError(f"{prefix} '{name}' has invalid type '{comp_type}'. Allowed: {', '.join(SUPPORTED_TYPES)}")

        # Check Pin boundaries (prevent boolean edge cases implicitly handled by type check)
        if type(pin) is not int:
            raise ValueError(f"{prefix} '{name}' pin must be an integer.")
            
        if not (ESP32_MIN_PIN <= pin <= ESP32_MAX_PIN):
            raise ValueError(f"{prefix} '{name}' pin {pin} is out of bounds ({ESP32_MIN_PIN}-{ESP32_MAX_PIN}).")

        # Check Input-Only pin rule
        if comp_type == "led" and pin in ESP32_INPUT_ONLY_PINS:
            raise ValueError(f"{prefix} LED '{name}' cannot use GPIO {pin} (GPIO 34-39 are input-only).")

        # Check for conflicts
        if pin in seen_pins:
            raise ValueError(f"GPIO {pin} collision between '{seen_pins[pin]}' and '{name}'.")
        
        seen_pins[pin] = name

    print("Config validation passed successfully.")
    return True

def generate_sketch(config):
    """ Generates C++ code string files (pins.h and .ino) from validated config"""
    project_name = config["project_name"]
    board = config ["board"]
    components = config["components"]
    
    pin_lines = [f"// SketchSeed pin map for {project_name} ({board})", ""]
    setup_lines = []
    loop_reads = []
    led_writes = []
    
    # Iterate over components to build C++ pin constants and setup logic
    for item in components:
        name = item["name"]
        kind = item["type"]
        pin = item["pin"]
        const_name = f"{name.upper()}_PIN"
        
        pin_lines.append(f"const int {const_name} = {pin};")
        
        if kind == "button":
            setup_lines.append(f" pinMode({const_name}, INPUT_PULLUP);")
            loop_reads.append( f" bool {name}_pressed = digitalRead({const_name}) == LOW;")
        elif kind == "led":
            setup_lines.append(f" pinMode({const_name}, OUTPUT);")
            setup_lines.append(f" digitalWrite({const_name}, LOW);")
            led_writes.append(name)
            
    # Determine starter behavior inside void loop()
    buttons = [item["name"] for item in components if item["type"] == "button"]
    if loop_reads and led_writes:
        first_button = buttons[0]
        loop_body = "\n".join(loop_reads) + "\n"
        for led in led_writes:
            loop_body += f" digitalWrite ({led.upper()}_PIN, {first_button}_pressed ? HIGH : LOW);\n"
            loop_comment = " // Button press drives LED state\n"
    elif led_writes:
        loop_body = ""
        for led in led_writes:
            loop_body += f" digitalWrite({led.upper()}_PIN, HIGH);\n delay(500);\n"
            loop_body += f" digitalWrite({led.upper()}_PIN, LOW);\n delay\n"
        loop_comment = " // Blink LED logic\n"
    else:
        loop_body = " delay(10);\n"
        loop_comment = " // Add button/LED loop logic here\n"
    # Assemble pins.h header file
    pins_h = "\n".join(
        ["#ifndef PINS_H", "#define PINS_H", "", *pin_lines, "", "#endif", ""]
    )
    
    # Assemble main .ino file
    ino = "\n".join(
        [
            f"// Generated by SketchSeed for {project_name}",
            ' #include "pins.h',
            "",
            "void_setup() {",
            *setup_lines,"}",
            "",
            "void loop() {",
            loop_comment.rstrip(),
            loop_body.rstrip(),
            "}",
            "",
        ]
    )
    return {"pins.h": pins_h, f"{project_name}.ino": ino}

def write_project(files, out_dir):
    """Writes generated C++ strings to disk inside out_dir."""
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)
    
    written_paths = []
    for filename, content in files.items():
        file_path = destination / filename
        file_path.write_text(content, encoding="utf-8")
        written_paths.append(file_path)
        
    return written_paths

def main():
    """Command-line entry point. """
    parser = argparse.ArgumentParser(
        description="Generate ESP32 starter sketches from JSON configs."
    )
    parser.add_argument("config", help="Path to JSON config file")
    parser.add_argument(
        "-o",
        "--out",
        default="build",
        help="Output directory (default: build)",
        )
    args = parser.parse_args()
    
    config = load_config(args.config)
    if not config:
        sys.exit(1)
        
    try:
        validate_config(config)
        files = generate_sketch(config)
        written = write_project(files, args.out)
        
        print(f"Successfully wrote {len(written)} file(s) to '{args.out}':")
        for p in written:
            print(f"  -{p}")
    except (ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
        
        
if __name__ == "__main__":
    main()

