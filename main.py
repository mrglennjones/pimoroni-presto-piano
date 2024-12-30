from presto import Presto
from machine import PWM, Pin
import time

# Initialize Presto
presto = Presto()
display = presto.display
touch = presto.touch
WIDTH, HEIGHT = display.get_bounds()

# Colors
WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)
DARK_GREY = display.create_pen(50, 50, 50)
RED = display.create_pen(230, 60, 45)

# Sound Output (PWM pin)
BUZZER_PIN = 43  # Use GPIO43 for the piezo buzzer
pwm = PWM(Pin(BUZZER_PIN))

# Keyboard Layout for 1 Octave
WHITE_KEYS = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
BLACK_KEYS = ['C#', 'D#', None, 'F#', 'G#', 'A#', None]

# Initialize dimensions
WHITE_KEY_WIDTH = WIDTH // len(WHITE_KEYS)  # White key width
BLACK_KEY_WIDTH = WHITE_KEY_WIDTH // 2      # Black keys are narrower
WHITE_KEY_HEIGHT = HEIGHT // 4             # White keys occupy 1/4th of the screen height
BLACK_KEY_HEIGHT = WHITE_KEY_HEIGHT // 1.5 # Black keys are shorter
KEYBOARD_Y = HEIGHT - WHITE_KEY_HEIGHT     # Keyboard starts from the bottom of the screen

# Base frequencies for 1 octave (C5 to B5)
BASE_FREQUENCIES = {
    'C': 523,  # C5
    'C#': 554, # C#5
    'D': 587,  # D5
    'D#': 622, # D#5
    'E': 659,  # E5
    'F': 698,  # F5
    'F#': 739, # F#5
    'G': 783,  # G5
    'G#': 830, # G#5
    'A': 880,  # A5
    'A#': 932, # A#5
    'B': 987   # B5
}

# Octave control
current_octave = 0  # Default octave (C5-B5)

# Calculate current octave label
def get_octave_label():
    return f"C{5 + current_octave}"  # Octave labels: C5, C6, C7, etc.

# Draw the keyboard
def draw_keyboard():
    # Draw white keys with borders
    for i, key in enumerate(WHITE_KEYS):
        x = int(i * WHITE_KEY_WIDTH)
        # Draw border
        display.set_pen(DARK_GREY)
        display.rectangle(x, int(KEYBOARD_Y), int(WHITE_KEY_WIDTH), int(WHITE_KEY_HEIGHT))
        # Draw the key inside the border
        display.set_pen(WHITE)
        display.rectangle(x + 1, int(KEYBOARD_Y) + 1, int(WHITE_KEY_WIDTH) - 2, int(WHITE_KEY_HEIGHT) - 2)
        # Draw the note label (adjusted position for white keys)
        text_x = x + (WHITE_KEY_WIDTH // 2) - 4
        text_y = int(KEYBOARD_Y) + (WHITE_KEY_HEIGHT // 3)
        display.set_pen(BLACK)
        display.text(key, int(text_x), int(text_y), scale=1)

    # Draw black keys with white text
    for i, key in enumerate(BLACK_KEYS):
        if key:
            x = int((i + 1) * WHITE_KEY_WIDTH - (BLACK_KEY_WIDTH // 2))
            # Draw the black key
            display.set_pen(BLACK)
            display.rectangle(x, int(KEYBOARD_Y), int(BLACK_KEY_WIDTH), int(BLACK_KEY_HEIGHT))
            # Center the text horizontally and vertically within the black key
            text_x = x + (BLACK_KEY_WIDTH // 2) - 4
            text_y = int(KEYBOARD_Y) + (BLACK_KEY_HEIGHT // 3)
            display.set_pen(WHITE)
            display.text(key, int(text_x), int(text_y), scale=1)

    # Draw octave controls
    display.set_pen(DARK_GREY)
    display.rectangle(10, 10, 60, 30)  # "Octave Down" button
    display.rectangle(WIDTH - 70, 10, 60, 30)  # "Octave Up" button
    display.set_pen(WHITE)
    display.text("DOWN", 15, 15, scale=1)
    display.text("UP", WIDTH - 65, 15, scale=1)

    # Draw current octave label
    display.set_pen(BLACK)
    display.text(get_octave_label(), WIDTH // 2 - 20, 15, scale=2)  # Centered label

# Determine which key is touched
def get_touched_key(touch_x, touch_y):
    # Check for black key touches first
    for i, key in enumerate(BLACK_KEYS):
        if key:
            x = int((i + 1) * WHITE_KEY_WIDTH - (BLACK_KEY_WIDTH // 2))
            if x <= touch_x <= x + int(BLACK_KEY_WIDTH) and int(KEYBOARD_Y) <= touch_y <= int(KEYBOARD_Y) + int(BLACK_KEY_HEIGHT):
                return key

    # Check for white key touches
    for i, key in enumerate(WHITE_KEYS):
        x = int(i * WHITE_KEY_WIDTH)
        if x <= touch_x <= x + int(WHITE_KEY_WIDTH) and int(KEYBOARD_Y) <= touch_y <= int(KEYBOARD_Y) + int(WHITE_KEY_HEIGHT):
            return key

    return None

# Play a tone
def play_tone(note):
    global current_octave
    freq = int(BASE_FREQUENCIES[note] * (2 ** current_octave))  # Ensure frequency is an integer
    print(f"DEBUG: Playing {note} at {freq} Hz (Octave {get_octave_label()})")
    pwm.freq(freq)
    pwm.duty_u16(32768)  # Fixed 50% duty cycle

# Stop the tone
def stop_tone():
    print("DEBUG: Stopping tone")
    pwm.duty_u16(0)

# Adjust octave
def adjust_octave(direction):
    global current_octave
    if direction == "up" and current_octave < 2:  # Limit to C7
        current_octave += 1
    elif direction == "down" and current_octave > 0:  # Limit to C5
        current_octave -= 1
    print(f"DEBUG: Octave changed to {get_octave_label()}")

# Main loop
try:
    draw_keyboard()
    presto.update()
    while True:
        presto.touch.poll()

        # Clear the screen
        display.set_pen(WHITE)
        display.clear()

        # Redraw the keyboard
        draw_keyboard()

        # Check for touch input
        touch_a = presto.touch_a
        if touch_a[2]:  # If touched
            touch_x, touch_y = touch_a[0], touch_a[1]

            # Check for octave control
            if 10 <= touch_x <= 70 and 10 <= touch_y <= 40:  # "Octave Down" button
                adjust_octave("down")
            elif WIDTH - 70 <= touch_x <= WIDTH - 10 and 10 <= touch_y <= 40:  # "Octave Up" button
                adjust_octave("up")
            else:
                # Check if a key was pressed
                key = get_touched_key(touch_x, touch_y)
                if key:
                    display.set_pen(RED)
                    if key in BLACK_KEYS:
                        # Highlight black key
                        x = int((BLACK_KEYS.index(key) + 1) * WHITE_KEY_WIDTH - (BLACK_KEY_WIDTH // 2))
                        display.rectangle(x, int(KEYBOARD_Y), int(BLACK_KEY_WIDTH), int(BLACK_KEY_HEIGHT))
                    else:
                        # Highlight white key
                        x = int(WHITE_KEYS.index(key) * WHITE_KEY_WIDTH)
                        display.rectangle(x, int(KEYBOARD_Y), int(WHITE_KEY_WIDTH), int(WHITE_KEY_HEIGHT))

                    # Play the note
                    play_tone(key)
        else:
            stop_tone()

        # Update the display
        presto.update()
        time.sleep(0.01)  # Control loop speed
finally:
    stop_tone()
    pwm.deinit()

