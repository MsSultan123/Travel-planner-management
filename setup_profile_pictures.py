import os
from PIL import Image, ImageDraw, ImageFont

# Create the profile pictures directory if it doesn't exist
profile_pictures_dir = 'static/uploads/profile_pictures'
os.makedirs(profile_pictures_dir, exist_ok=True)

# Create a default profile picture
def create_default_profile_picture():
    # Create a new image with a blue background
    img = Image.new('RGB', (200, 200), '#1877f2')
    draw = ImageDraw.Draw(img)
    
    # Draw a circle for the avatar
    draw.ellipse([40, 40, 160, 160], fill='white')
    
    # Draw a simple avatar shape
    draw.ellipse([70, 70, 130, 110], fill='#1877f2')  # Head
    draw.rectangle([85, 110, 115, 150], fill='#1877f2')  # Body
    
    # Save the image
    img.save(os.path.join(profile_pictures_dir, 'default.jpg'), 'JPEG', quality=95)
    print('Created default profile picture')

# Create the default profile picture
create_default_profile_picture()

# Copy existing profile pictures to the correct location
source_files = {
    'eiffel_tower_original.jpg': 'user1_profile.jpg',
    'great_wall_original.jpg': 'user2_profile.jpg',
    'sundarbans_original.jpg': 'user3_profile.jpg'
}

for source, dest in source_files.items():
    try:
        if os.path.exists(source):
            # Open and resize the image
            img = Image.open(source)
            img = img.resize((200, 200), Image.Resampling.LANCZOS)
            # Save to profile pictures directory
            img.save(os.path.join(profile_pictures_dir, dest), 'JPEG', quality=95)
            print(f'Copied and resized {source} to {dest}')
    except Exception as e:
        print(f'Error processing {source}: {str(e)}') 