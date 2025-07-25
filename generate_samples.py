#!/usr/bin/env python3
"""
Sample Image Generator for GoatMorpho Testing
Creates synthetic goat images for testing the measurement system
"""

import cv2
import numpy as np
import os


def create_sample_goat_image(filename="sample_goat.jpg", width=800, height=600):
    """
    Create a simple synthetic goat image for testing
    This creates a basic side-profile silhouette that should be detectable
    """
    # Create a blank image with grass-like background
    image = np.ones((height, width, 3), dtype=np.uint8) * 180  # Light gray background
    
    # Add some grass texture at bottom
    grass_height = height // 4
    image[height-grass_height:, :] = [34, 139, 34]  # Forest green
    
    # Add some texture to grass
    for i in range(0, width, 20):
        cv2.line(image, (i, height-grass_height), (i+10, height-grass_height-20), (0, 100, 0), 2)
    
    # Define goat body proportions (side view)
    goat_width = width // 2
    goat_height = height // 2
    start_x = width // 4
    start_y = height // 3
    
    # Goat body (rectangle)
    body_rect = [
        [start_x, start_y + goat_height//3],
        [start_x + goat_width//2, start_y + goat_height//3],
        [start_x + goat_width//2, start_y + goat_height],
        [start_x, start_y + goat_height]
    ]
    cv2.fillPoly(image, [np.array(body_rect)], (101, 67, 33))  # Brown color
    
    # Goat head (circle)
    head_center = (start_x - 40, start_y + goat_height//3 + 20)
    head_radius = 35
    cv2.circle(image, head_center, head_radius, (101, 67, 33), -1)
    
    # Ears (triangles)
    ear1 = np.array([[head_center[0]-25, head_center[1]-30],
                     [head_center[0]-15, head_center[1]-50],
                     [head_center[0]-5, head_center[1]-35]])
    ear2 = np.array([[head_center[0]+5, head_center[1]-35],
                     [head_center[0]+15, head_center[1]-50],
                     [head_center[0]+25, head_center[1]-30]])
    cv2.fillPoly(image, [ear1], (101, 67, 33))
    cv2.fillPoly(image, [ear2], (101, 67, 33))
    
    # Eyes
    cv2.circle(image, (head_center[0]-10, head_center[1]-10), 3, (0, 0, 0), -1)
    
    # Nose/snout
    snout = np.array([[head_center[0]-50, head_center[1]],
                      [head_center[0]-35, head_center[1]+10],
                      [head_center[0]-35, head_center[1]-10]])
    cv2.fillPoly(image, [snout], (101, 67, 33))
    
    # Legs (4 rectangles)
    leg_width = 15
    leg_height = goat_height // 2
    
    # Front legs
    leg1_x = start_x + 30
    leg2_x = start_x + 60
    # Back legs  
    leg3_x = start_x + goat_width//2 - 60
    leg4_x = start_x + goat_width//2 - 30
    
    leg_start_y = start_y + goat_height
    
    for leg_x in [leg1_x, leg2_x, leg3_x, leg4_x]:
        cv2.rectangle(image, 
                     (leg_x, leg_start_y), 
                     (leg_x + leg_width, leg_start_y + leg_height), 
                     (101, 67, 33), -1)
        # Hooves
        cv2.rectangle(image,
                     (leg_x, leg_start_y + leg_height),
                     (leg_x + leg_width, leg_start_y + leg_height + 10),
                     (0, 0, 0), -1)
    
    # Tail
    tail_start = (start_x + goat_width//2, start_y + goat_height//2)
    tail_end = (start_x + goat_width//2 + 40, start_y + goat_height//2 + 30)
    cv2.line(image, tail_start, tail_end, (101, 67, 33), 8)
    
    # Add some simple landmarks that MediaPipe might detect
    # Shoulder point
    cv2.circle(image, (start_x + 30, start_y + goat_height//3 + 10), 3, (255, 0, 0), -1)
    # Hip point
    cv2.circle(image, (start_x + goat_width//2 - 30, start_y + goat_height//3 + 10), 3, (255, 0, 0), -1)
    
    # Add reference ruler (optional)
    ruler_start_x = width - 100
    ruler_start_y = 50
    cv2.rectangle(image, (ruler_start_x, ruler_start_y), (ruler_start_x + 80, ruler_start_y + 20), (255, 255, 255), -1)
    cv2.rectangle(image, (ruler_start_x, ruler_start_y), (ruler_start_x + 80, ruler_start_y + 20), (0, 0, 0), 2)
    cv2.putText(image, "20cm", (ruler_start_x + 15, ruler_start_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    # Add measurement lines to show what should be measured
    # Height line
    cv2.line(image, (start_x - 60, start_y + goat_height//3), 
             (start_x - 60, leg_start_y + leg_height), (0, 255, 0), 2)
    cv2.putText(image, "Height", (start_x - 100, start_y + goat_height//2), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    
    # Length line
    cv2.line(image, (head_center[0] - head_radius, start_y + goat_height + 30), 
             (start_x + goat_width//2, start_y + goat_height + 30), (0, 255, 0), 2)
    cv2.putText(image, "Length", (start_x + goat_width//4, start_y + goat_height + 45), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    
    return image


def create_real_goat_recommendations():
    """
    Create an info image with tips for taking real goat photos
    """
    info_img = np.ones((600, 800, 3), dtype=np.uint8) * 240  # Light background
    
    # Title
    cv2.putText(info_img, "Perfect Goat Photo Guidelines", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    guidelines = [
        "1. Side profile view (90 degrees)",
        "2. All four legs visible",
        "3. Good lighting (natural daylight)",
        "4. Goat standing upright",
        "5. Clear, uncluttered background", 
        "6. Sharp focus, no motion blur",
        "7. Include reference object (ruler, coin)",
        "8. High resolution (800x600 minimum)",
        "",
        "Avoid:",
        "- Front/back views", 
        "- Angled shots",
        "- Poor lighting/shadows",
        "- Blurry or low-res images",
        "- Partial goat views"
    ]
    
    y_pos = 100
    for line in guidelines:
        if line.startswith("Avoid:"):
            cv2.putText(info_img, line, (50, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        elif line.startswith("-"):
            cv2.putText(info_img, line, (70, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        elif line:
            cv2.putText(info_img, line, (50, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        y_pos += 30
    
    return info_img


def main():
    """Generate sample images for testing"""
    # Create media directories if they don't exist
    os.makedirs("media/goat_images/samples", exist_ok=True)
    
    print("Generating sample goat image...")
    sample_goat = create_sample_goat_image()
    cv2.imwrite("media/goat_images/samples/sample_goat_profile.jpg", sample_goat)
    print("✓ Created: media/goat_images/samples/sample_goat_profile.jpg")
    
    print("Generating photo guidelines image...")
    guidelines_img = create_real_goat_recommendations()
    cv2.imwrite("media/goat_images/samples/photo_guidelines.jpg", guidelines_img)
    print("✓ Created: media/goat_images/samples/photo_guidelines.jpg")
    
    # Create a simple test pattern that should definitely be detected
    print("Generating detection test pattern...")
    test_pattern = np.ones((400, 600, 3), dtype=np.uint8) * 255
    
    # Draw a simple human-like figure that MediaPipe should detect
    # Head
    cv2.circle(test_pattern, (300, 80), 30, (0, 0, 0), -1)
    # Body
    cv2.line(test_pattern, (300, 110), (300, 250), (0, 0, 0), 20)
    # Arms
    cv2.line(test_pattern, (300, 150), (250, 180), (0, 0, 0), 10)
    cv2.line(test_pattern, (300, 150), (350, 180), (0, 0, 0), 10)
    # Legs
    cv2.line(test_pattern, (300, 250), (270, 320), (0, 0, 0), 10)
    cv2.line(test_pattern, (300, 250), (330, 320), (0, 0, 0), 10)
    
    cv2.imwrite("media/goat_images/samples/detection_test.jpg", test_pattern)
    print("✓ Created: media/goat_images/samples/detection_test.jpg")
    
    print("\nSample images created successfully!")
    print("You can now test these images with the GoatMorpho system:")
    print("1. sample_goat_profile.jpg - Synthetic goat for testing")
    print("2. detection_test.jpg - Simple pattern for pose detection testing")
    print("3. photo_guidelines.jpg - Guidelines for taking real goat photos")


if __name__ == "__main__":
    main()
