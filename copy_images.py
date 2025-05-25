import os
import shutil

# Create the destinations directory if it doesn't exist
os.makedirs('static/images/destinations', exist_ok=True)

# Map of source files to destination names
image_mapping = {
    'eiffel_tower_original.jpg': 'eiffel_tower.jpg',
    'grand_canyon_original.webp': 'grand_canyon.jpg',
    'disneyland_original.webp': 'disneyland.jpg',
    'great_wall_original.jpg': 'great_wall.jpg',
    'sundarbans_original.jpg': 'sundarbans.jpg',
    'coxs_bazar_original.jpg': 'coxs_bazar.jpg',
    'sentosa_original.jpg': 'sentosa.jpg'
}

# Copy and rename the images
for source, dest in image_mapping.items():
    try:
        # Convert webp to jpg if needed
        if source.endswith('.webp'):
            # For webp files, we'll just copy them as is
            shutil.copy2(source, f'static/images/destinations/{dest}')
        else:
            shutil.copy2(source, f'static/images/destinations/{dest}')
        print(f'Successfully copied {source} to {dest}')
    except Exception as e:
        print(f'Error copying {source}: {str(e)}')

# Create placeholder images for missing destinations
missing_destinations = ['coxs_bazar.jpg', 'sentosa.jpg']
for dest in missing_destinations:
    try:
        # Copy the placeholder image for missing destinations
        shutil.copy2('static/images/placeholder.jpg', f'static/images/destinations/{dest}')
        print(f'Created placeholder for {dest}')
    except Exception as e:
        print(f'Error creating placeholder for {dest}: {str(e)}') 