import streamlit as st
import pandas as pd
from pathlib import Path

# --- Page Configuration ---
# Set the layout to wide for better use of screen space
st.set_page_config(
    page_title="Face Attribute Viewer",
    page_icon="👤",
    layout="wide",
)


# --- Caching Function ---
@st.cache_data
def load_data(uploaded_file):
    """
    Loads data from the uploaded CSV file into a pandas DataFrame.
    Uses caching to avoid reloading data on every interaction.
    """
    try:
        df = pd.read_csv(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        return None


# --- Main Application ---
st.title("👤 Face Attribute Viewer")
st.markdown(
    "This tool helps you visually inspect images, their corresponding face crops, and curated facial attributes. It is **not** sensitive to uppercase or lowercase in names or filenames.")

# --- Sidebar for User Inputs ---
with st.sidebar:
    st.header("⚙️ Setup Panel")

    # 1. CSV file uploader
    uploaded_file = st.file_uploader(
        "1. Upload your attributes CSV file",
        type=["csv"],
        help="The CSV file should contain all parameters, including 'image_filename' and 'name'."
    )

    # 2. Original Image directory input
    image_base_dir_path = st.text_input(
        "2. Enter path to ORIGINAL image directory",
        help="This is the top-level folder for the full original images."
    )
    # 3. Face Image directory input (Optional)
    face_image_base_dir_path = st.text_input(
        "3. Enter path to FACE image directory (Optional)",
        help="This is the top-level folder for the corresponding face-only images."
    )

# --- Main Content Area ---

# Check if required inputs are provided
if not uploaded_file or not image_base_dir_path:
    st.info(
        "👋 Welcome! Please use the sidebar to upload your CSV file and provide the image directory path(s) to begin.")
    st.markdown("""
    ### How to Prepare Your Data:
    1.  **Create Image Directory Structures:**
        -   Have a main folder for your **original images** (e.g., `original_dataset`).
        -   If you have them, create another main folder for your **face images** (e.g., `face_dataset`).
        -   Inside both, create a subfolder for each person. The subfolder names must match the person's name (case-insensitively).
        -   Place all images for that person inside their respective subfolders. The filenames should also match.

    2.  **Create a CSV File:**
        -   The CSV must contain `image_filename` and `name` columns.
        -   **Full columns list:** `image_filename`, `name`, `nationality`, `occupation`, `gender`, `age_group`, `hairstyle`, `facial_features`, `accessories`, `expression`, `skin_tone`, `face_shape`.
    """)
else:
    # Convert the input string path to a Path object for robust path handling
    image_base_dir = Path(image_base_dir_path)

    # Validate if the provided path is actually a directory
    if not image_base_dir.is_dir():
        st.error(f"The ORIGINAL image path is not a valid directory: {image_base_dir_path}")
    else:
        # Load the data from the uploaded CSV
        df = load_data(uploaded_file)

        if df is not None:
            # --- Column Validation ---
            required_columns = ["image_filename", "name"]
            if not all(col in df.columns for col in required_columns):
                st.error(f"The CSV file is missing 'image_filename' and/or 'name' columns.")
            else:
                # --- Case-Insensitive Person Selection ---
                unique_names_map = {name.lower(): name for name in df['name'].dropna().unique()[::-1]}
                person_list = sorted(unique_names_map.values())

                selected_person = st.sidebar.selectbox(
                    "4. Select a Person to View",
                    person_list
                )

                st.sidebar.success(f"Setup complete. Now showing results for **{selected_person}**.")

                # --- Display Filtered Results ---
                st.header(f"Displaying Images and Attributes for: **{selected_person}**", divider='rainbow')

                person_df = df[df['name'].str.lower() == selected_person.lower()].copy()

                # --- Find Paths and File Maps ---
                # Original Images
                all_orig_subdirs = [p for p in image_base_dir.iterdir() if p.is_dir()]
                orig_person_folder_path = next(
                    (path for path in all_orig_subdirs if path.name.lower() == selected_person.lower()), None)

                # Face Images (if path provided)
                face_person_folder_path = None
                if face_image_base_dir_path:
                    face_image_base_dir = Path(face_image_base_dir_path)
                    if face_image_base_dir.is_dir():
                        all_face_subdirs = [p for p in face_image_base_dir.iterdir() if p.is_dir()]
                        face_person_folder_path = next(
                            (path for path in all_face_subdirs if path.name.lower() == selected_person.lower()), None)

                if person_df.empty:
                    st.warning(f"No data found for '{selected_person}' in the CSV file.")
                elif not orig_person_folder_path:
                    st.error(
                        f"Originals Folder Not Found: Could not find a subfolder for '{selected_person}' in the directory provided (checked case-insensitively).")
                else:
                    st.write(f"Found **{len(person_df)}** images for this person.")

                    # Create file maps for both directories
                    orig_filename_map = {f.name.lower(): f.name for f in orig_person_folder_path.iterdir() if
                                         f.is_file()}
                    face_filename_map = {}
                    if face_person_folder_path:
                        face_filename_map = {f.name.lower(): f.name for f in face_person_folder_path.iterdir() if
                                             f.is_file()}

                    # Iterate through each row (each image) for the selected person
                    for index, row in person_df.iterrows():
                        st.markdown("---")
                        csv_filename = row["image_filename"]

                        # --- Create a three-column layout ---
                        col1, col2, col3 = st.columns([1, 1, 2])

                        # --- Column 1: Display Original Image ---
                        with col1:
                            st.caption("Original Image")
                            correct_orig_filename = orig_filename_map.get(csv_filename.lower())
                            if correct_orig_filename:
                                image_path = orig_person_folder_path / correct_orig_filename
                                st.image(str(image_path), caption=correct_orig_filename, use_container_width=True)
                            else:
                                st.warning(f"File not found in original folder.")

                        # --- Column 2: Display Face Image ---
                        with col2:
                            st.caption("Face Image")
                            if face_person_folder_path:
                                correct_face_filename = face_filename_map.get(csv_filename.lower())
                                if correct_face_filename:
                                    face_image_path = face_person_folder_path / correct_face_filename
                                    st.image(str(face_image_path), caption=correct_face_filename,
                                             use_container_width=True)
                                else:
                                    st.warning(f"File not found in face folder.")
                            else:
                                if face_image_base_dir_path:
                                    st.warning(f"Folder for '{selected_person}' not found in face directory.")
                                else:
                                    st.info("No face image directory provided.")

                        # --- Column 3: Display Attributes Table ---
                        with col3:
                            st.caption("Attributes")
                            attributes = row.to_frame().reset_index()
                            attributes.columns = ["Attribute", "Value"]
                            st.dataframe(attributes, use_container_width=True, hide_index=True, height=460)
