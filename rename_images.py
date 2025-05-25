import os

# Define the new names for all image files
rename_mapping = {
    'eiffel_tower_original.jpg': 'eiffel_tower_original.jpg',  # Already renamed
    'great_wall_original.jpg': 'great_wall_original.jpg',      # Already renamed
    'sundarbans_original.jpg': 'sundarbans_original.jpg',      # Already renamed
    '2843.webp': 'disneyland_original.webp',
    'mather-point-2021.webp': 'grand_canyon_original.webp'
}

# Rename the files
for old_name, new_name in rename_mapping.items():
    try:
        if os.path.exists(old_name):
            if old_name != new_name:  # Only rename if the names are different
                os.rename(old_name, new_name)
                print(f'Successfully renamed {old_name} to {new_name}')
        else:
            print(f'File {old_name} not found')
    except Exception as e:
        print(f'Error renaming {old_name}: {str(e)}') 