import os
import glob
import subprocess

AUDIO_DIR = "/tmp/elevance_walkthrough/audio"
FINAL_VIDEO = "/Users/parthbiradar/ACE/Elevance-project/demo_walkthrough.mp4"

# 1. Find recorded raw webm video
webm_files = glob.glob("/tmp/elevance_walkthrough/video_raw/*.webm")
if not webm_files:
    raise RuntimeError("No raw webm video found in /tmp/elevance_walkthrough/video_raw/")
# Sort by modification time to pick the latest
webm_files.sort(key=os.path.getmtime, reverse=True)
raw_video = webm_files[0]

print(f"Raw video path: {raw_video}")

# 2. Concat audio files
audio_order = ["intro.m4a", "chat.m4a", "tickets.m4a", "kb.m4a", "ocr.m4a", "time_metrics.m4a"]
audio_list_file = os.path.join(AUDIO_DIR, "audio_concat.txt")
with open(audio_list_file, "w") as f:
    for a in audio_order:
        f.write(f"file '{os.path.join(AUDIO_DIR, a)}'\n")

merged_audio = os.path.join(AUDIO_DIR, "full_audio.m4a")
cmd_merge_audio = [
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", audio_list_file,
    "-c", "copy",
    merged_audio
]
subprocess.run(cmd_merge_audio, check=True)
print(f"Merged audio generated at: {merged_audio}")

# 3. Mux video and audio together into Full HD MP4
print("Muxing browser video recording and narration audio into final demo_walkthrough.mp4...")
cmd_mux = [
    "ffmpeg", "-y",
    "-i", raw_video,
    "-i", merged_audio,
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "22",
    "-c:a", "aac",
    "-b:a", "192k",
    "-pix_fmt", "yuv420p",
    "-shortest",
    FINAL_VIDEO
]
subprocess.run(cmd_mux, check=True)

# 4. Probe final video
res = subprocess.run([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration,size:stream=width,height,codec_name",
    "-of", "default=noprint_wrappers=1",
    FINAL_VIDEO
], capture_output=True, text=True, check=True)

print("\nSUCCESS! FINAL WEBSITE WALKTHROUGH VIDEO COMPILED:")
print(f"Destination: {FINAL_VIDEO}")
print(res.stdout)

