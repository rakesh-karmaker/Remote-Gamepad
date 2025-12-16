import vgamepad as vg

# Minimum change required to send axis update to vgamepad
AXIS_EPSILON = 0.02  # ~2% movement threshold

def apply_payload_to_gamepad(gamepad: vg.VX360Gamepad, payload: dict, current_axis_values: dict):
    ev_type = payload.get('type')
    code = payload.get('code')
    state = payload.get('state')
    if ev_type == 'Key':
        handle_button(gamepad, code, state == 1)
    elif ev_type == 'Absolute':
        if code in ["ABS_X", "ABS_Y", "ABS_RX", "ABS_RY", "ABS_Z", "ABS_RZ"]:
            axis_map = {
                "ABS_X": 0,
                "ABS_Y": 1,
                "ABS_RX": 2,
                "ABS_RY": 3,
                "ABS_Z": 4,
                "ABS_RZ": 5,
            }
            axis = axis_map[code]
            if code in ["ABS_Z", "ABS_RZ"]:
                value = (state / 255.0) * 2 - 1
            else:
                value = state / 32767.0
            handle_axis(gamepad, axis, value, current_axis_values)
        elif code == "ABS_HAT0X":
            handle_hat(gamepad, (state, 0))
        elif code == "ABS_HAT0Y":
            handle_hat(gamepad, (0, state * -1))

def handle_button(gamepad: vg.VX360Gamepad, button: str, pressed: bool):
    vg_button = {
        "BTN_SOUTH": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
        "BTN_EAST": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
        "BTN_WEST": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
        "BTN_NORTH": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
        "BTN_TL": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
        "BTN_TR": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
        "BTN_START": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
        "BTN_SELECT": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
        "BTN_THUMBL": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
        "BTN_THUMBR": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    }.get(button, None)

    if vg_button is not None:
        if pressed:
            gamepad.press_button(vg_button)
        else:
            gamepad.release_button(vg_button)
        gamepad.update()

def handle_axis(gamepad: vg.VX360Gamepad, axis: int, value: float, current_axis_values: dict):
    # Joysticks: only update when movement is meaningful
    if axis == 0:  # Left joystick X
        if abs(value - current_axis_values[0]) >= AXIS_EPSILON:
            current_axis_values[0] = value
            gamepad.left_joystick_float(x_value_float=value, y_value_float=current_axis_values[1])
            gamepad.update()
    elif axis == 1:  # Left joystick Y
        if abs(value - current_axis_values[1]) >= AXIS_EPSILON:
            current_axis_values[1] = value
            gamepad.left_joystick_float(x_value_float=current_axis_values[0], y_value_float=value)
            gamepad.update()
    elif axis == 2:  # Right joystick X
        if abs(value - current_axis_values[2]) >= AXIS_EPSILON:
            current_axis_values[2] = value
            gamepad.right_joystick_float(x_value_float=value, y_value_float=current_axis_values[3])
            gamepad.update()
    elif axis == 3:  # Right joystick Y
        if abs(value - current_axis_values[3]) >= AXIS_EPSILON:
            current_axis_values[3] = value
            gamepad.right_joystick_float(x_value_float=current_axis_values[2], y_value_float=value)
            gamepad.update()
    elif axis == 4:  # Left trigger
        trigger_value = int((value + 1) / 2 * 255)  # Scale from -1.0 to 1.0 to 0 to 255
        gamepad.left_trigger(value=trigger_value)
        gamepad.update()
    elif axis == 5:  # Right trigger
        trigger_value = int((value + 1) / 2 * 255)  # Scale from -1.0 to 1.0 to 0 to 255
        gamepad.right_trigger(value=trigger_value)
        gamepad.update()

def handle_hat(gamepad: vg.VX360Gamepad, value: tuple):
    x, y = value
    if x == -1:
        gamepad.left_joystick(x_value=-32767, y_value=0)
    if x == 1:
        gamepad.left_joystick(x_value=32767, y_value=0)
    if y == -1:
        gamepad.left_joystick(x_value=0, y_value=-32767)
    if y == 1:
        gamepad.left_joystick(x_value=0, y_value=32767)
    if x == 0 and y == 0:
        gamepad.left_joystick(x_value=0, y_value=0)
    gamepad.update()

