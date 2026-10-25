import pytest
import json
from project import (load_config, validate_config, generate_sketch, write_project)


@pytest.fixture
def valid_config_data():
    """Returns a valid ESP32 configuration dictionary for testing."""
    return {
        "board": "esp32",
        "project_name": "smart_led",
        "components": [
            {"name": "button", "type": "button", "pin":4},
            {"name": "status_led", "type": "led", "pin": 5},
        ],
    }

# 1. TEST LOAD_CONFIG
def test_load_config_valid(tmp_path):
    # Creates a temporary valid JSON file
    config_file = tmp_path / "valid.json"
    data = { "board": "esp32","project_name": "test_proj", "components": []}
    config_file.write_text(json.dumps(data), encoding="utf-8")
    
    loaded = load_config(config_file)
    assert loaded == data

def test_load_config_missing_file():
    # Should catch FileNotFoundError and return None
    assert load_config("non_existent_file.json") is None
    
def test_load_config_invalid_json(tmp_path):
    # Create an invalid syntax JSON file
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json", encoding="utf-8")
    
    # Should catch JSONDecodeError and return None
    assert load_config(bad_file) is None
    
def test_load_config_not_a_dict(tmp_path):
    # Create JSON that parses into a list instead of a dict
    list_file = tmp_path / "list.json"
    list_file.write_text('["esp32", "smart_led"]', encoding="utf-8")
    
    assert load_config(list_file) is None
    

# 2. TEST VALIDATE_CONFIG
def test_validate_config_valid(valid_config_data):
    assert validate_config(valid_config_data) is True
    
def test_validate_config_invalid_board(valid_config_data):
    valid_config_data["board"] = "arduino_uno"
    with pytest.raises(ValueError, match="Unsupported board"):
        validate_config(valid_config_data)
        
def test_validate_config_invalid_project_name(valid_config_data):
    valid_config_data["project_name"] = "123_invalid_name!"
    with pytest.raises(ValueError, match="Invalid project name"):
        validate_config(valid_config_data)
        
def test_validate_config_input_only_pin_for_led(valid_config_data):
    # Assign LED to GPIO 34 (input-only on ESP32)
    valid_config_data["components"][1]["pin"] = 34
    with pytest.raises(ValueError, match="input-only"):
        validate_config(valid_config_data)
        
def test_validate_config_pin_collision(valid_config_data):
    # Set both button and LED to pin 4
    valid_config_data["components"][1]["pin"] = 4
    with pytest.raises(ValueError, match="collision"):
        validate_config(valid_config_data)
        
def test_validate_config_boolean_pin(valid_config_data):
    # Pass a boolean true as pin number
    valid_config_data["components"][0]["pin"] = True
    with pytest.raises(ValueError, match="must be an integer"):
        validate_config(valid_config_data)
        
# 3. TEST GENERATE_SKETCH
def test_generate_sketch(valid_config_data):
    files = generate_sketch(valid_config_data)
    
    assert"pins.h"in files
    assert "smart_led.ino" in files
    
    # Check pins.h header generation
    assert "const int BUTTON_PIN = 4;" in files["pins.h"]
    assert "const int STATUS_LED_PIN = 5;" in files["pins.h"]
    
    # Check .ino code generation
    assert "pinMode(BUTTON_PIN, INPUT_PULLUP);" in files["smart_led.ino"]
    assert "pinMode(STATUS_LED_PIN, OUTPUT);" in files["smart_led.ino"]
    
    
# 4. TEST WRITE_PROJECT
def test_write_project(tmp_path):
    fake_files = {
        "pins.h": "// pins header",
        "demo.ino": "// main sketch"
}
    out_dir = tmp_path / "build_output"
    
    written = write_project(fake_files, out_dir)
    
    assert len(written) == 2
    assert (out_dir / "pins.h").exists()
    assert (out_dir / "demo.ino").exists()
    assert (out_dir / "pins.h").read_text(encoding="utf-8") == "// pins header"