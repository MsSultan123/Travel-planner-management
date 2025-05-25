from PIL import Image, ImageDraw
import os

# Create the destinations directory if it doesn't exist
os.makedirs('static/images/destinations', exist_ok=True)

# Create a new image with a transparent background
img = Image.new('RGBA', (2000, 1000), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw clouds
for i in range(20):
    # Random cloud positions and sizes
    x = i * 200
    y = 200 + (i % 3) * 200
    size = 100 + (i % 4) * 50
    
    # Draw cloud circles
    for j in range(3):
        draw.ellipse([
            x + j * 50, y,
            x + j * 50 + size, y + size
        ], fill=(255, 255, 255, 50))

# Save the image
img.save('static/images/destinations/clouds.png')
print('Created cloud pattern image') 