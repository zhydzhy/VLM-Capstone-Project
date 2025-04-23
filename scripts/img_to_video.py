import os
import subprocess

def create_video():
    image_folder = '/home/vlmteam/VLM_Ccapstone-Project/images/rgb'
    output_file = os.path.join('/home/vlmteam/VLM_Ccapstone-Project/images', 'video.mp4')
    
    # Get sorted list of numeric filenames
    files = [f for f in os.listdir(image_folder) if f.endswith('.png')]
    numbers = sorted([int(f.split('.')[0]) for f in files])
    
    # Verify frame difference
    diffs = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
    if not all(d == 4 for d in diffs):
        print("Warning: Frame numbers don't have consistent 4-step difference!")
    
    # FFmpeg command (25 fps = 40ms per frame, assuming 4-step = 0.16s real-time)
    cmd = [
        'ffmpeg', '-y', '-framerate', '25',
        '-pattern_type', 'sequence', '-i', f'{image_folder}/%06d.png',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', output_file
    ]
    
    subprocess.run(cmd, check=True)

if __name__ == '__main__':
    create_video()