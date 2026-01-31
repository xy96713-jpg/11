import os
import subprocess
import json
import sys

def extract_frames(video_path, timestamps, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    results = []
    
    for i, ts_ms in enumerate(timestamps):
        ts_sec = ts_ms / 1000.0
        frame_filename = f"frame_{int(ts_sec)}s.jpg"
        output_path = os.path.join(output_dir, frame_filename)
        
        # ffmpeg command to extract a single frame at a specific timestamp
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(ts_sec),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            results.append({"timestamp": ts_sec, "path": output_path})
            print(f"[*] Extracted frame at {ts_sec}s -> {frame_filename}", file=sys.stderr)
        except Exception as e:
            print(f"[!] FFmpeg error at {ts_sec}s: {e}", file=sys.stderr)
            
    return results

if __name__ == "__main__":
    v_path = sys.argv[1]
    j_path = sys.argv[2]
    out_dir = sys.argv[3]
    
    with open(j_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract timestamps from recommend_chapter_info
    chapters = data.get("aweme_detail", {}).get("recommend_chapter_info", {}).get("recommend_chapter_list", [])
    timestamps = [c.get("timestamp", 0) for c in chapters]
    
    # Add some key mid-points or manual checks if needed
    if not timestamps:
        timestamps = [5000, 15000, 30000, 60000, 120000] # Fallback
        
    extracted = extract_frames(v_path, timestamps, out_dir)
    print(json.dumps(extracted, ensure_ascii=False))
