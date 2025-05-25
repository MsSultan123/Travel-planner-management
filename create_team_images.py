from PIL import Image, ImageDraw, ImageFont
import os

def create_team_image(name, role, output_path):
    # Create a 400x400 image with a light gray background
    img = Image.new('RGB', (400, 400), color='#f8f9fa')
    draw = ImageDraw.Draw(img)
    
    # Draw a circle in the center
    circle_center = (200, 200)
    circle_radius = 150
    draw.ellipse([circle_center[0]-circle_radius, circle_center[1]-circle_radius,
                  circle_center[0]+circle_radius, circle_center[1]+circle_radius],
                 fill='#e9ecef')
    
    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    # Draw name
    name_bbox = draw.textbbox((0, 0), name, font=font)
    name_width = name_bbox[2] - name_bbox[0]
    name_height = name_bbox[3] - name_bbox[1]
    draw.text((200 - name_width/2, 200 - name_height/2), name, fill='#495057', font=font)
    
    # Save the image
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)

# Create team member images
team_members = [
    ('lead.jpg', 'John Doe', 'Project Lead'),
    ('developer.jpg', 'Sarah Smith', 'Lead Developer'),
    ('designer.jpg', 'Mike Johnson', 'UI/UX Designer')
]

for filename, name, role in team_members:
    output_path = os.path.join('static', 'images', 'team', filename)
    create_team_image(name, role, output_path)
    print(f"Created team member image: {output_path}") 