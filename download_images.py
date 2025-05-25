import os
import requests
from PIL import Image
from io import BytesIO

# Create the directory if it doesn't exist
os.makedirs('static/images/destinations', exist_ok=True)

# Sample images from Unsplash (free to use)
image_urls = {
    'eiffel_tower.jpg': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb',
    'grand_canyon.jpg': 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429',
    'disneyland.jpg': 'https://images.unsplash.com/photo-1464983953574-0892a716854b',
    'great_wall.jpg': 'https://images.unsplash.com/photo-1501785888041-af3ef285b470',
    'sundarbans.jpg': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e',
    'coxs_bazar.jpg': 'https://images.unsplash.com/photo-1502086223501-7ea6ecd79368',
    'sentosa.jpg': 'https://images.unsplash.com/photo-1465101046530-73398c7f28ca'
}

for filename, url in image_urls.items():
    try:
        # Download the image
        response = requests.get(url)
        if response.status_code == 200:
            # Open the image and resize it
            img = Image.open(BytesIO(response.content))
            img = img.resize((400, 300), Image.Resampling.LANCZOS)
            
            # Save the image
            img.save(f'static/images/destinations/{filename}', 'JPEG', quality=85)
            print(f'Successfully downloaded and saved {filename}')
        else:
            print(f'Failed to download {filename}')
    except Exception as e:
        print(f'Error processing {filename}: {str(e)}') 