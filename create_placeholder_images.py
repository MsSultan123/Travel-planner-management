from PIL import Image, ImageDraw, ImageFont
import os

# Create the destinations directory if it doesn't exist
os.makedirs('static/images/destinations', exist_ok=True)

# Create placeholder images for missing destinations
missing_destinations = [
    {'name': 'Cox\'s Bazar', 'filename': 'coxs_bazar.jpg'},
    {'name': 'Sentosa Island', 'filename': 'sentosa.jpg'}
]

for dest in missing_destinations:
    # Create a new image with a white background
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    # Draw the destination name
    text = dest['name']
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (800 - text_width) / 2
    y = (600 - text_height) / 2
    
    draw.text((x, y), text, font=font, fill='black')
    
    # Save the image
    img.save(f'static/images/destinations/{dest["filename"]}')
    print(f'Created placeholder for {dest["name"]}') 