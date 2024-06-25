# ------------------------------------------------------------------------------------ #
# Made by Darshan
# ------------------------------------------------------------------------------------ #
# Application for Number Plate labelling
# ------------------------------------------------------------------------------------ #

import PySimpleGUI as sg
import os
from PIL import Image
import io

# Function to convert image to bytes
def convert_image_to_bytes(image_path, resize=None):
    """Convert an image to bytes, optionally resizing it."""
    img = Image.open(image_path)
    if resize:
        img = img.resize(resize, Image.Resampling.LANCZOS)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


# Function to extract the proposed number plate from the filename
def extract_numplate(filename):
    return filename.split('_')[-1].split('.')[0]


# Function to update the labels file
def update_labels(filename, numplate):
    labels = {}
    if os.path.exists('labels.txt'):
        with open('labels.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split(',')
                labels[parts[0]] = parts[1]

    labels[filename] = numplate

    with open('labels.txt', 'w') as f:
        for key, value in labels.items():
            f.write(f"{key},{value}\n")


# Function to load images from the script directory
def load_images_from_directory():
    folder = os.path.dirname(os.path.abspath(__file__))
    file_list = os.listdir(folder)
    image_files = [
        f
        for f in file_list
        if os.path.isfile(os.path.join(folder, f))
           and f.lower().endswith((".png", ".gif", ".jpg", ".jpeg"))
    ]
    return folder, image_files


# Function to load the last labeled image from labels.txt
def get_last_labeled_image(image_files):
    if not os.path.exists('labels.txt'):
        return 0
    with open('labels.txt', 'r') as f:
        lines = f.readlines()
        if not lines:
            return 0
        last_image = lines[-1].split(',')[0]
        if last_image in image_files:
            return image_files.index(last_image)
    return 0


# Function to read the visibility state from a file
def read_visibility_state():
    if os.path.exists('visibility_state.txt'):
        with open('visibility_state.txt', 'r') as file:
            state = file.read().strip()
            return state == 'True'
    return False  # Default to hidden if no file exists


# Function to save the visibility state to a file
def save_visibility_state(state):
    with open('visibility_state.txt', 'w') as file:
        file.write(str(state))


# Function to load labeled images from labels.txt
def load_labeled_images():
    labeled_images = set()
    if os.path.exists('labels.txt'):
        with open('labels.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split(',')
                labeled_images.add(parts[0])
    return labeled_images


# Read initial visibility state from file
column_visible = read_visibility_state()

# Second column: Image viewer and navigation
image_viewer_column = [
    [sg.Text(size=(40, 1), key="-TOUT-")],
    [sg.Image(key="-IMAGE-")],
    [
        sg.Button("Back", key="-BACK-"),
        sg.Button("Exit", key="-EXIT-"),
        sg.Button("Next", key="-NEXT-"),
    ],
]

# Third column: Annotation tools
annotation_column = [
    [sg.Text("Proposed Numplate:")],
    [sg.Text(size=(15, 2), key="-NUMPLATE-")],
    [sg.Text("Accept?")],
    [
        sg.Button("YES", key="-YES-"),
        sg.Text(" ", key="-UPDATED-"),
        sg.Button("NO", key="-NO-"),
    ],
    [sg.Column([
        [sg.HSeparator()],
        [sg.Text("Enter Numplate:")],
        [sg.In(size=(25, 1), key="-MANUAL NUMPLATE-")],
        [sg.Button("SUBMIT", key="-SUBMIT-")],
    ], visible=column_visible, key="-TOGGLE-", size=(300, 100))],  # Fixed size for the column
]

# Full layout
layout = [
    [
        sg.Column(image_viewer_column),
        sg.VSeperator(),
        sg.Column(annotation_column),
    ]
]

window = sg.Window("Image Viewer", layout, finalize=True, resizable=False)

current_image_index = 0
image_files = []
labeled_images = load_labeled_images()

# Load images from script directory
folder, image_files = load_images_from_directory()
current_image_index = get_last_labeled_image(image_files)


# Function to update image display
def update_image_display(index):
    if index < 0 or index >= len(image_files):
        return
    filename = os.path.join(folder, image_files[index])
    window["-TOUT-"].update(filename)
    image_bytes = convert_image_to_bytes(filename, resize=(400, 400))
    window["-IMAGE-"].update(data=image_bytes)
    numplate = extract_numplate(image_files[index])
    window["-NUMPLATE-"].update(numplate)
    if image_files[index] in labeled_images:
        window["-UPDATED-"].update("Labelled")
    else:
        window["-UPDATED-"].update("")

# Initialize the display
update_image_display(current_image_index)

# Run the Event Loop
while True:
    event, values = window.read(timeout=1000)
    if event == "Exit" or event == sg.WIN_CLOSED or event == "-EXIT-":
        break

    if event in ("-BACK-", "-NEXT-"):
        if event == "-BACK-" and current_image_index > 0:
            current_image_index -= 1
        elif event == "-NEXT-" and current_image_index < len(image_files) - 1:
            current_image_index += 1

        update_image_display(current_image_index)

    elif event == "-YES-":
        filename = image_files[current_image_index]
        numplate = window["-NUMPLATE-"].get()
        update_labels(filename, numplate)
        labeled_images.add(filename)
        window["-UPDATED-"].update("Saved")
        window.refresh()
        sg.time.sleep(1)
        window["-UPDATED-"].update("Labelled")

        if current_image_index < len(image_files) - 1:
            current_image_index += 1
            update_image_display(current_image_index)

    elif event == "-NO-":
        column_visible = not window['-TOGGLE-'].visible
        window['-TOGGLE-'].update(visible=column_visible)
        save_visibility_state(column_visible)

    elif event == "-SUBMIT-":
        filename = image_files[current_image_index]
        numplate = values["-MANUAL NUMPLATE-"].replace(" ", "")
        if numplate:
            update_labels(filename, numplate)
            labeled_images.add(filename)
            window["-NUMPLATE-"].update(numplate)
        window["-MANUAL NUMPLATE-"].update("")
        window["-UPDATED-"].update("Saved")
        window.refresh()
        sg.time.sleep(1)
        window["-UPDATED-"].update("Labelled")

        if current_image_index < len(image_files) - 1:
            current_image_index += 1
            update_image_display(current_image_index)
        window['-TOGGLE-'].update(visible=False)
        save_visibility_state(False)

window.close()
