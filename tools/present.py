#!/usr/bin/env python3
"""
Wrapper around presenterm that adds image zoom support.

Usage: python3 present.py <markdown_file> [presenterm args...]

Keys:
  z  - Toggle zoom on current slide's image (opens/closes Preview)
  [  - Manually adjust: slide counter back (if tracking drifts)
  ]  - Manually adjust: slide counter forward (if tracking drifts)
"""

import os
import re
import sys
import pty
import signal
import select
import fcntl
import termios
import tty
import subprocess

DEBUG = os.environ.get("PRESENT_DEBUG") == "1"

def log(msg):
    if DEBUG:
        with open("/tmp/present_debug.log", "a") as f:
            f.write(msg + "\n")

def parse_slides(md_path):
    """
    Returns list of (pause_count, [image_paths]) per presenterm slide.
    Accounts for front matter generating an extra intro slide.
    """
    base_dir = os.path.dirname(os.path.abspath(md_path))
    with open(md_path) as f:
        content = f.read()

    # Check if there's a front matter (presenterm creates an intro slide for it)
    has_front_matter = content.lstrip().startswith("---")

    raw_slides = re.split(r'^<!-- end_slide -->', content, flags=re.MULTILINE)
    result = []

    # If front matter exists, presenterm shows it as slide 0 (intro) with 0 pauses
    if has_front_matter:
        result.append((0, []))  # intro slide from front matter

    for slide_text in raw_slides:
        pauses = len(re.findall(r'<!-- pause -->', slide_text))
        images = [
            os.path.join(base_dir, img)
            for img in re.findall(r'!\[.*?\]\(([^)]+)\)', slide_text)
            if os.path.exists(os.path.join(base_dir, img))
        ]
        result.append((pauses, images))

    return result

def sync_size(master_fd):
    sz = fcntl.ioctl(sys.stdin.fileno(), termios.TIOCGWINSZ, b'\x00' * 8)
    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, sz)

def open_preview(images):
    """Open images in Preview and bring to front. Returns a sentinel process."""
    subprocess.Popen(
        ["open", "-a", "Preview"] + images,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).wait()
    subprocess.Popen(
        ["osascript", "-e", 'tell application "Preview" to activate'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).wait()
    # Return a background watcher so we know Preview is "open"
    return subprocess.Popen(
        ["osascript", "-e",
         'tell application "Preview"\n'
         '  repeat while (count of windows) > 0\n'
         '    delay 0.3\n'
         '  end repeat\n'
         'end tell'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

def close_preview(zoom_proc):
    """Close Preview and refocus iTerm."""
    if zoom_proc and zoom_proc.poll() is None:
        zoom_proc.terminate()
    subprocess.Popen(
        ["osascript", "-e",
         'tell application "Preview" to close every window\n'
         'tell application "iTerm" to activate'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <markdown_file> [presenterm args...]")
        sys.exit(1)

    md_path = sys.argv[1]
    slides = parse_slides(md_path)
    total = len(slides)

    img_count = sum(len(imgs) for _, imgs in slides)
    print(f"Found {img_count} zoomable images across {total} slides")
    print("Keys: z=zoom  [/]=adjust slide counter if it drifts")
    if DEBUG:
        print(f"Debug log: /tmp/present_debug.log")
    print("Starting presenterm...\n")

    cur = 0       # current slide index
    pause = 0     # pauses consumed on current slide

    master_fd, slave_fd = pty.openpty()
    proc = subprocess.Popen(
        ["presenterm"] + sys.argv[1:],
        stdin=slave_fd, stdout=slave_fd, stderr=slave_fd, close_fds=True,
    )
    os.close(slave_fd)
    sync_size(master_fd)
    signal.signal(signal.SIGWINCH, lambda *_: sync_size(master_fd))

    old_attrs = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin)

    zoom_proc = None
    stdin_fd = sys.stdin.fileno()
    pending_g = False

    def nav_next():
        nonlocal cur, pause
        if pause < slides[cur][0]:
            pause += 1
        elif cur < total - 1:
            cur += 1
            pause = 0
        log(f"NEXT -> slide={cur} pause={pause}/{slides[cur][0]} imgs={bool(slides[cur][1])}")

    def nav_prev():
        nonlocal cur, pause
        if pause > 0:
            pause -= 1
        elif cur > 0:
            cur -= 1
            pause = slides[cur][0]
        log(f"PREV -> slide={cur} pause={pause}/{slides[cur][0]}")

    def nav_first():
        nonlocal cur, pause
        cur, pause = 0, 0
        log(f"FIRST -> slide=0")

    def nav_last():
        nonlocal cur, pause
        cur = total - 1
        pause = slides[cur][0]
        log(f"LAST -> slide={cur}")

    try:
        while proc.poll() is None:
            rlist, _, _ = select.select([stdin_fd, master_fd], [], [], 0.1)
            for fd in rlist:
                if fd == master_fd:
                    try:
                        data = os.read(master_fd, 65536)
                    except OSError:
                        break
                    if data:
                        os.write(sys.stdout.fileno(), data)

                elif fd == stdin_fd:
                    data = os.read(stdin_fd, 1024)
                    if not data:
                        continue

                    # --- Zoom toggle ---
                    if data == b'z':
                        if zoom_proc and zoom_proc.poll() is None:
                            close_preview(zoom_proc)
                            zoom_proc = None
                        else:
                            imgs = slides[cur][1] if cur < total else []
                            log(f"ZOOM slide={cur} images={imgs}")
                            if imgs:
                                zoom_proc = open_preview(imgs)
                        continue

                    # --- Manual slide counter adjust ---
                    if data == b'[':
                        if cur > 0:
                            cur -= 1
                            pause = 0
                        log(f"ADJUST- -> slide={cur}")
                        continue
                    if data == b']':
                        if cur < total - 1:
                            cur += 1
                            pause = 0
                        log(f"ADJUST+ -> slide={cur}")
                        continue

                    # --- Navigation tracking ---
                    if data in (b'\x1b[C', b'\x1b[B', b'\x1b[6~'):
                        nav_next()
                    elif data in (b'\x1b[D', b'\x1b[A', b'\x1b[5~'):
                        nav_prev()
                    elif len(data) == 1:
                        ch = chr(data[0])
                        if ch in 'lj \r\n':
                            nav_next()
                        elif ch in 'hk':
                            nav_prev()
                        elif ch == 'G':
                            nav_last()
                        elif ch == 'g':
                            if pending_g:
                                nav_first()
                                pending_g = False
                            else:
                                pending_g = True
                                os.write(master_fd, data)
                                continue
                        else:
                            pending_g = False

                    pending_g = False
                    os.write(master_fd, data)

    except OSError:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, old_attrs)
        close_preview(zoom_proc)
        proc.wait()

if __name__ == "__main__":
    main()
