# agent/tools.py — Complete Multi-Purpose Jarvis Tool Suite

import os
import subprocess
import webbrowser
import platform
import datetime
import shutil
import json
import re
import urllib.parse
import urllib.request
import tempfile
import threading
import time
from pathlib import Path

# ── Optional imports with graceful fallbacks ───────────
try:
    import pandas as pd
    PANDAS_OK = True
except ImportError:
    PANDAS_OK = False

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

try:
    import pyautogui
    PYAUTOGUI_OK = True
except ImportError:
    PYAUTOGUI_OK = False

try:
    import pyperclip
    PYPERCLIP_OK = True
except ImportError:
    PYPERCLIP_OK = False

try:
    from PIL import Image, ImageGrab
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    from plyer import notification
    PLYER_OK = True
except ImportError:
    PLYER_OK = False

try:
    from bs4 import BeautifulSoup
    BS4_OK = True
except ImportError:
    BS4_OK = False

try:
    import pywhatkit
    PYWHATKIT_OK = True
except ImportError:
    PYWHATKIT_OK = False

from config import NOTES_DIR
from core.search import web_search as _web_search
from agent.memory import remember, recall, forget, set_preference, get_preference

os.makedirs(NOTES_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════
#  WEB TOOLS
# ══════════════════════════════════════════════════════

def search_web(query: str) -> str:
    """Search the web for current information."""
    return _web_search(query)

def open_website(url: str) -> str:
    """Open a URL in the default browser."""
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url} in browser."

def fetch_webpage(url: str) -> str:
    """Fetch and extract readable text from a webpage."""
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")
        if BS4_OK:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            text = soup.get_text(separator="\n")
            text = "\n".join(
                line.strip() for line in text.splitlines() if line.strip()
            )
            return text[:3000]
        else:
            text = re.sub(r"<[^>]+>", "", html)
            return text[:3000]
    except Exception as e:
        return f"Could not fetch page: {e}"

def summarize_url(url: str) -> str:
    """Fetch a webpage and return a summary."""
    content = fetch_webpage(url)
    if content.startswith("Could not"):
        return content
    return content[:2000]

# ══════════════════════════════════════════════════════
#  APP TOOLS
# ══════════════════════════════════════════════════════

APP_MAP = {
    "youtube":       "https://youtube.com",
    "google":        "https://google.com",
    "gmail":         "https://mail.google.com",
    "github":        "https://github.com",
    "stackoverflow": "https://stackoverflow.com",
    "chatgpt":       "https://chat.openai.com",
    "reddit":        "https://reddit.com",
    "linkedin":      "https://linkedin.com",
    "twitter":       "https://twitter.com",
    "instagram":     "https://instagram.com",
    "facebook":      "https://facebook.com",
    "netflix":       "https://netflix.com",
    "spotify":       "spotify",
    "notepad":       "notepad.exe",
    "calculator":    "calc.exe",
    "explorer":      "explorer.exe",
    "vscode":        "code",
    "chrome":        "chrome",
    "discord":       "discord",
    "whatsapp": "shell:appsFolder\\WhatsApp.WhatsApp_8wekyb3d8bbwe!App",
    "telegram":      "telegram",
    "task manager":  "taskmgr.exe",
    "paint":         "mspaint.exe",
    "word":          "winword.exe",
    "excel":         "excel.exe",
    "powerpoint":    "powerpnt.exe",
    "cmd":           "cmd.exe",
    "powershell":    "powershell.exe",
    "settings":      "ms-settings:",
    "maps":          "https://maps.google.com",
    "weather":       "https://weather.com",
    "translate":     "https://translate.google.com",
    "nvidia":          "shell:appsFolder\\NVIDIACorp.NVIDIAControlPanel_56jybvy8sckqj!NVIDIAControlPanel",
    "nvidia app":      "shell:appsFolder\\NVIDIACorp.NVIDIAControlPanel_56jybvy8sckqj!NVIDIAControlPanel",
    "nvidia control":  "shell:appsFolder\\NVIDIACorp.NVIDIAControlPanel_56jybvy8sckqj!NVIDIAControlPanel",
    "geforce":         "shell:appsFolder\\NVIDIACorp.NVIDIAControlPanel_56jybvy8sckqj!NVIDIAControlPanel",
}

def open_app(app_name: str) -> str:
    """Open an application or website by name."""
    name  = app_name.lower().strip()
    match = APP_MAP.get(name)

    if match:
        if match.startswith("http"):
            webbrowser.open(match)
            return f"Opened {app_name} in browser."
        elif match.endswith(":"):
            os.startfile(match)
            return f"Opened {app_name}."
        else:
            try:
                subprocess.Popen(match, shell=True)
                return f"Opened {app_name}."
            except Exception as e:
                return f"Failed to open {app_name}: {e}"
    else:
        # Search common install locations automatically
        search_paths = [
            os.environ.get("PROGRAMFILES", "C:\\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", ""),
            os.environ.get("APPDATA", ""),
        ]

        for base in search_paths:
            if not base:
                continue
            for root, dirs, files in os.walk(base):
                for file in files:
                    if (app_name.lower() in file.lower()
                            and file.endswith(".exe")):
                        full_path = os.path.join(root, file)
                        try:
                            subprocess.Popen(f'"{full_path}"', shell=True)
                            return f"Found and launched: {full_path}"
                        except Exception as e:
                            return f"Found but failed to launch: {e}"

        # Last resort — try Windows search
        try:
            subprocess.Popen(
                f'explorer shell:appsFolder',
                shell=True
            )
            # Try direct command
            subprocess.Popen(app_name, shell=True)
            return f"Attempted to launch {app_name}."
        except Exception as e:
            return f"Could not find or open {app_name}: {e}"

def close_app(app_name: str) -> str:
    """Close a running application."""
    try:
        result = subprocess.run(
            f"taskkill /f /im {app_name}",
            shell=True, capture_output=True, text=True
        )
        return result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return f"Could not close {app_name}: {e}"

# ══════════════════════════════════════════════════════
#  SYSTEM TOOLS
# ══════════════════════════════════════════════════════

def run_command(command: str) -> str:
    """Run a terminal/shell command and return output."""
    try:
        result = subprocess.run(
            command, shell=True,
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output if output else "Command executed with no output."
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."
    except Exception as e:
        return f"Command failed: {e}"

def get_datetime() -> str:
    """Get current date and time."""
    now = datetime.datetime.now()
    return now.strftime("Today is %A, %B %d %Y. The time is %I:%M %p.")

def get_system_info() -> str:
    """Get system information."""
    info = {
        "OS":      platform.system() + " " + platform.release(),
        "Machine": platform.machine(),
        "Python":  platform.python_version(),
    }
    if PSUTIL_OK:
        info["CPU Usage"]     = f"{psutil.cpu_percent(interval=1)}%"
        info["RAM Usage"]     = f"{psutil.virtual_memory().percent}%"
        info["RAM Available"] = f"{psutil.virtual_memory().available // (1024**3)} GB"
        battery = psutil.sensors_battery()
        if battery:
            info["Battery"] = (
                f"{int(battery.percent)}% "
                f"{'(Charging)' if battery.power_plugged else '(On Battery)'}"
            )
    return "\n".join(f"{k}: {v}" for k, v in info.items())

def get_battery() -> str:
    """Get battery status."""
    if not PSUTIL_OK:
        return "psutil not installed."
    battery = psutil.sensors_battery()
    if not battery:
        return "No battery detected."
    status = "Charging" if battery.power_plugged else "On battery"
    return f"Battery at {int(battery.percent)}% — {status}."

def get_running_processes() -> str:
    """Get top running processes."""
    if not PSUTIL_OK:
        return "psutil not installed."
    procs = []
    for p in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
        try:
            procs.append(p.info)
        except:
            pass
    top = sorted(procs, key=lambda x: x["cpu_percent"], reverse=True)[:10]
    return "\n".join(
        f"{p['name']}: CPU {p['cpu_percent']}% RAM {p['memory_percent']:.1f}%"
        for p in top
    )

def kill_process(name: str) -> str:
    """Kill a process by name."""
    if not PSUTIL_OK:
        return "psutil not installed."
    killed = 0
    for p in psutil.process_iter(["name"]):
        try:
            if name.lower() in p.info["name"].lower():
                p.kill()
                killed += 1
        except:
            pass
    return f"Killed {killed} process(es) matching '{name}'."

def get_disk_usage() -> str:
    """Get disk usage for all drives."""
    if not PSUTIL_OK:
        return run_command("wmic logicaldisk get size,freespace,caption")
    parts = psutil.disk_partitions()
    lines = []
    for p in parts:
        try:
            usage = psutil.disk_usage(p.mountpoint)
            lines.append(
                f"{p.mountpoint}: {usage.used // (1024**3)}GB used / "
                f"{usage.total // (1024**3)}GB total ({usage.percent}%)"
            )
        except:
            pass
    return "\n".join(lines) if lines else "Could not get disk info."

def take_screenshot(filename: str = "") -> str:
    """Take a screenshot and save it."""
    if not PIL_OK:
        return "Pillow not installed. Run: pip install pillow"
    try:
        if not filename:
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        if not os.path.isabs(filename):
            filename = os.path.join("data", filename)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        img = ImageGrab.grab()
        img.save(filename)
        return f"Screenshot saved: {filename}"
    except Exception as e:
        return f"Screenshot failed: {e}"

def copy_to_clipboard(text: str) -> str:
    """Copy text to clipboard."""
    if not PYPERCLIP_OK:
        return "pyperclip not installed."
    try:
        pyperclip.copy(text)
        return "Copied to clipboard."
    except Exception as e:
        return f"Clipboard error: {e}"

def get_clipboard() -> str:
    """Get current clipboard content."""
    if not PYPERCLIP_OK:
        return "pyperclip not installed."
    try:
        return pyperclip.paste() or "Clipboard is empty."
    except Exception as e:
        return f"Clipboard error: {e}"

def show_notification(title: str, message: str) -> str:
    """Show a desktop notification."""
    if PLYER_OK:
        try:
            notification.notify(
                title=title, message=message,
                app_name="Jarvis", timeout=5
            )
            return f"Notification shown: {title}"
        except:
            pass
    ps = (
        f'powershell -c "[void][Windows.UI.Notifications.ToastNotificationManager,'
        f'Windows.UI.Notifications,ContentType=WindowsRuntime]"'
    )
    run_command(ps)
    return f"Notification sent: {title}"

def set_reminder(message: str, seconds: int) -> str:
    """Set a reminder after N seconds."""
    def _remind():
        time.sleep(int(seconds))
        show_notification("Jarvis Reminder", message)
    threading.Thread(target=_remind, daemon=True).start()
    minutes = int(seconds) // 60
    unit    = f"{minutes} minute(s)" if minutes > 0 else f"{seconds} second(s)"
    return f"Reminder set for {unit}: {message}"

def start_timer(seconds: int, label: str = "Timer") -> str:
    """Start a countdown timer."""
    def _timer():
        time.sleep(int(seconds))
        show_notification(f"⏰ {label}", f"Your {label} is done!")
    threading.Thread(target=_timer, daemon=True).start()
    return f"{label} started for {seconds} seconds."

# ══════════════════════════════════════════════════════
#  FILE TOOLS
# ══════════════════════════════════════════════════════

def read_file(path: str) -> str:
    """Read contents of any text file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content[:4000] if len(content) > 4000 else content
    except Exception as e:
        return f"Could not read file: {e}"

def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    try:
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File written: {path}"
    except Exception as e:
        return f"Could not write file: {e}"

def append_file(path: str, content: str) -> str:
    """Append content to an existing file."""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + content)
        return f"Appended to {path}."
    except Exception as e:
        return f"Could not append: {e}"

def delete_file(path: str) -> str:
    """Delete a file."""
    try:
        os.remove(path)
        return f"Deleted {path}."
    except Exception as e:
        return f"Could not delete: {e}"

def copy_file(src: str, dst: str) -> str:
    """Copy a file."""
    try:
        shutil.copy2(src, dst)
        return f"Copied {src} to {dst}."
    except Exception as e:
        return f"Could not copy: {e}"

def move_file(src: str, dst: str) -> str:
    """Move a file."""
    try:
        shutil.move(src, dst)
        return f"Moved {src} to {dst}."
    except Exception as e:
        return f"Could not move: {e}"

def list_files(directory: str = ".") -> str:
    """List files in a directory."""
    try:
        items = []
        for item in os.listdir(directory):
            full  = os.path.join(directory, item)
            size  = os.path.getsize(full) if os.path.isfile(full) else 0
            label = "📁" if os.path.isdir(full) else "📄"
            items.append(f"{label} {item} ({size} bytes)" if size else f"{label} {item}")
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"Could not list: {e}"

def open_file(path: str) -> str:
    """Open a file with its default application."""
    try:
        os.startfile(path)
        return f"Opened {path}."
    except Exception as e:
        return f"Could not open: {e}"

def create_folder(path: str) -> str:
    """Create a new folder."""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder created: {path}"
    except Exception as e:
        return f"Could not create folder: {e}"

def rename_file(old_path: str, new_path: str) -> str:
    """Rename a file."""
    try:
        os.rename(old_path, new_path)
        return f"Renamed to {new_path}."
    except Exception as e:
        return f"Could not rename: {e}"

def zip_files(source: str, output: str) -> str:
    """Zip a file or folder."""
    try:
        shutil.make_archive(output.replace(".zip", ""), "zip", source)
        return f"Zipped to {output}."
    except Exception as e:
        return f"Could not zip: {e}"

# ══════════════════════════════════════════════════════
#  DATA TOOLS
# ══════════════════════════════════════════════════════

def read_csv(path: str, rows: int = 20) -> str:
    """Read and summarize a CSV file."""
    if not PANDAS_OK:
        return "pandas not installed."
    try:
        # Expand common shortcuts
        path = path.replace("Desktop",   os.path.join(os.path.expanduser("~"), "Desktop"))
        path = path.replace("Documents", os.path.join(os.path.expanduser("~"), "Documents"))
        path = path.replace("Downloads", os.path.join(os.path.expanduser("~"), "Downloads"))

        df      = pd.read_csv(path)
        summary  = f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n"
        summary += f"Columns: {', '.join(df.columns.tolist())}\n\n"
        summary += f"First {min(rows, len(df))} rows:\n"
        summary += df.head(rows).to_string(index=False)
        return summary
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Could not read CSV: {e}"

def analyze_csv(path: str, query: str) -> str:
    """Analyze a CSV with a natural language query."""
    if not PANDAS_OK:
        return "pandas not installed."
    try:
        # Expand common path shortcuts
        path = path.replace("Desktop", os.path.join(os.path.expanduser("~"), "Desktop"))
        path = path.replace("Documents", os.path.join(os.path.expanduser("~"), "Documents"))
        path = path.replace("Downloads", os.path.join(os.path.expanduser("~"), "Downloads"))

        df      = pd.read_csv(path)
        query_l = query.lower().strip()
        result  = f"File: {path}\nShape: {df.shape[0]} rows x {df.shape[1]} cols\nColumns: {list(df.columns)}\n\n"

        # ── ID / value lookup ──────────────────────────
        # Handles: patient_id == '00013' or just '00013' or ID 00013
        id_match = re.search(
            r"(?:==|is|=|:)?\s*['\"]?(\w+)['\"]?",
            query, re.IGNORECASE
        )
        # Try to find matching row by searching ALL columns
        if id_match:
            search_val = id_match.group(1).strip().strip("'\"")
            for col in df.columns:
                # Try exact match first
                mask = df[col].astype(str).str.strip() == search_val
                if mask.any():
                    matched = df[mask]
                    result += f"Found {len(matched)} matching row(s) where {col} = '{search_val}':\n\n"
                    result += matched.to_string(index=False)
                    return result
                # Try case-insensitive
                mask = df[col].astype(str).str.lower().str.strip() == search_val.lower()
                if mask.any():
                    matched = df[mask]
                    result += f"Found {len(matched)} matching row(s) where {col} = '{search_val}':\n\n"
                    result += matched.to_string(index=False)
                    return result
            result += f"No rows found matching '{search_val}' in any column."
            return result

        # ── Aggregations ───────────────────────────────
        if "total" in query_l or "sum" in query_l:
            numeric = df.select_dtypes(include="number")
            result += "Column totals:\n"
            for col in numeric.columns:
                result += f"  {col}: {numeric[col].sum():,.2f}\n"

        elif "average" in query_l or "mean" in query_l:
            numeric = df.select_dtypes(include="number")
            result += "Column averages:\n"
            for col in numeric.columns:
                result += f"  {col}: {numeric[col].mean():,.2f}\n"

        elif "count" in query_l or "how many" in query_l:
            result += f"Total rows: {len(df)}\n"
            for col in df.columns:
                result += f"  {col}: {df[col].nunique()} unique values\n"

        elif "max" in query_l or "highest" in query_l:
            numeric = df.select_dtypes(include="number")
            result += "Maximum values:\n"
            for col in numeric.columns:
                result += f"  {col}: {numeric[col].max():,.2f}\n"

        elif "min" in query_l or "lowest" in query_l:
            numeric = df.select_dtypes(include="number")
            result += "Minimum values:\n"
            for col in numeric.columns:
                result += f"  {col}: {numeric[col].min():,.2f}\n"

        else:
            result += df.describe().to_string()

        return result[:3000]
    except FileNotFoundError:
        return f"File not found: {path}. Please check the path."
    except Exception as e:
        return f"Analysis failed: {e}"

def read_excel(path: str, sheet: str = "") -> str:
    """Read an Excel file."""
    if not PANDAS_OK:
        return "pandas not installed."
    try:
        df      = pd.read_excel(path, sheet_name=sheet or 0)
        summary  = f"Shape: {df.shape[0]} rows x {df.shape[1]} cols\n"
        summary += f"Columns: {', '.join(df.columns.tolist())}\n\n"
        summary += df.head(20).to_string(index=False)
        return summary
    except Exception as e:
        return f"Could not read Excel: {e}"

def csv_to_json(csv_path: str, json_path: str) -> str:
    """Convert CSV to JSON."""
    if not PANDAS_OK:
        return "pandas not installed."
    try:
        df = pd.read_csv(csv_path)
        df.to_json(json_path, orient="records", indent=2)
        return f"Converted to JSON: {json_path}"
    except Exception as e:
        return f"Conversion failed: {e}"

def read_json_file(path: str) -> str:
    """Read and format a JSON file."""
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return json.dumps(data, indent=2)[:3000]
    except Exception as e:
        return f"Could not read JSON: {e}"

def write_csv(path: str, data: str) -> str:
    """Write data to a CSV file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
        return f"CSV written: {path}"
    except Exception as e:
        return f"Could not write CSV: {e}"

# ══════════════════════════════════════════════════════
#  CODE TOOLS
# ══════════════════════════════════════════════════════

def run_python(code: str) -> str:
    """Execute Python code and return output."""
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False
        ) as f:
            f.write(code)
            tmp = f.name
        result = subprocess.run(
            f"python {tmp}",
            shell=True, capture_output=True, text=True, timeout=30
        )
        os.unlink(tmp)
        output = result.stdout.strip() or result.stderr.strip()
        return output if output else "Code ran with no output."
    except Exception as e:
        return f"Execution failed: {e}"

def run_script(path: str) -> str:
    """Run an existing Python script."""
    try:
        result = subprocess.run(
            f"python {path}",
            shell=True, capture_output=True, text=True, timeout=60
        )
        return result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return f"Script failed: {e}"

def install_package(package: str) -> str:
    """Install a Python package via pip."""
    return run_command(f"pip install {package}")

# ══════════════════════════════════════════════════════
#  NOTES TOOLS
# ══════════════════════════════════════════════════════

def create_note(title: str, content: str) -> str:
    """Create and save a note."""
    safe = "".join(c for c in title if c.isalnum() or c in " _-").strip()
    path = os.path.join(NOTES_DIR, f"{safe}.txt")
    ts   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    body = f"Title: {title}\nDate: {ts}\n\n{content}"
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return f"Note saved: {safe}.txt"

def list_notes() -> str:
    """List all saved notes."""
    notes = [f for f in os.listdir(NOTES_DIR) if f.endswith(".txt")]
    if not notes:
        return "No notes found."
    return "Notes:\n" + "\n".join(f"- {n}" for n in sorted(notes))

def read_note(title: str) -> str:
    """Read a note by title."""
    safe = "".join(c for c in title if c.isalnum() or c in " _-").strip()
    path = os.path.join(NOTES_DIR, f"{safe}.txt")
    if not os.path.exists(path):
        matches = [
            f for f in os.listdir(NOTES_DIR) if title.lower() in f.lower()
        ]
        if matches:
            path = os.path.join(NOTES_DIR, matches[0])
        else:
            return f"Note not found: {title}"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def append_note(title: str, content: str) -> str:
    """Add to an existing note."""
    safe = "".join(c for c in title if c.isalnum() or c in " _-").strip()
    path = os.path.join(NOTES_DIR, f"{safe}.txt")
    if not os.path.exists(path):
        return create_note(title, content)
    ts = datetime.datetime.now().strftime("%H:%M")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n[{ts}] {content}")
    return f"Added to note: {title}"

def delete_note(title: str) -> str:
    """Delete a note."""
    safe = "".join(c for c in title if c.isalnum() or c in " _-").strip()
    path = os.path.join(NOTES_DIR, f"{safe}.txt")
    if os.path.exists(path):
        os.remove(path)
        return f"Note deleted: {title}"
    return f"Note not found: {title}"

def search_notes(query: str) -> str:
    """Search notes by content."""
    results = []
    for fname in os.listdir(NOTES_DIR):
        if not fname.endswith(".txt"):
            continue
        fpath = os.path.join(NOTES_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            if query.lower() in f.read().lower():
                results.append(fname)
    if not results:
        return f"No notes found containing '{query}'."
    return "Matching notes:\n" + "\n".join(f"- {r}" for r in results)

def open_note(title: str) -> str:
    """Open a note in Notepad."""
    safe = "".join(c for c in title if c.isalnum() or c in " _-").strip()
    path = os.path.join(NOTES_DIR, f"{safe}.txt")
    if not os.path.exists(path):
        matches = [
            f for f in os.listdir(NOTES_DIR) if title.lower() in f.lower()
        ]
        if matches:
            path = os.path.join(NOTES_DIR, matches[0])
        else:
            return f"Note not found: {title}"
    os.startfile(path)
    return f"Opened note: {title}"

# ══════════════════════════════════════════════════════
#  MESSAGING & SHARE TOOLS
# ══════════════════════════════════════════════════════

def send_whatsapp(phone: str, message: str, hour: int = -1, minute: int = -1) -> str:
    """Send a WhatsApp message via pywhatkit."""
    if not PYWHATKIT_OK:
        return whatsapp_web(phone, message)
    try:
        now = datetime.datetime.now()
        if int(hour) < 0 or int(minute) < 0:
            send_time    = now + datetime.timedelta(minutes=1)
            hour, minute = send_time.hour, send_time.minute
        pywhatkit.sendwhatmsg(phone, message, int(hour), int(minute), wait_time=20)
        return f"WhatsApp message scheduled to {phone}."
    except Exception as e:
        return f"WhatsApp send failed: {e}"

def whatsapp_web(phone: str = "", message: str = "") -> str:
    """Open WhatsApp Web with optional pre-filled message."""
    if phone:
        clean   = re.sub(r"[^\d+]", "", phone)
        encoded = urllib.parse.quote(message)
        url     = f"https://web.whatsapp.com/send?phone={clean}&text={encoded}"
    else:
        url = "https://web.whatsapp.com"
    webbrowser.open(url)
    return f"Opened WhatsApp Web{' for ' + phone if phone else ''}."

def draft_email(to: str, subject: str, body: str) -> str:
    """Open Gmail compose."""
    params = urllib.parse.urlencode({"to": to, "su": subject, "body": body})
    webbrowser.open(f"https://mail.google.com/mail/?view=cm&{params}")
    return f"Gmail compose opened for {to}."

def share_via_browser(content: str, platform: str = "gmail") -> str:
    """Share content via a platform."""
    encoded = urllib.parse.quote(content)
    urls = {
        "gmail":    f"https://mail.google.com/mail/?view=cm&body={encoded}",
        "twitter":  f"https://twitter.com/intent/tweet?text={encoded}",
        "telegram": f"https://t.me/share/url?url=&text={encoded}",
        "whatsapp": f"https://web.whatsapp.com/send?text={encoded}",
        "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url=&summary={encoded}",
    }
    url = urls.get(platform.lower())
    if not url:
        return f"Unknown platform: {platform}"
    webbrowser.open(url)
    return f"Opened {platform} in browser."

def send_telegram(message: str, bot_token: str = "", chat_id: str = "") -> str:
    """Send a Telegram message via bot API."""
    if not bot_token:
        bot_token = get_preference("telegram_token")
    if not chat_id:
        chat_id = get_preference("telegram_chat_id")
    if "Not set" in bot_token or "Not set" in chat_id:
        return (
            "Telegram credentials not set. Tell Jarvis: "
            "'save my telegram token as YOUR_TOKEN' and "
            "'save my telegram chat id as YOUR_ID'"
        )
    try:
        url  = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = urllib.parse.urlencode(
            {"chat_id": chat_id, "text": message}
        ).encode()
        urllib.request.urlopen(url, data=data, timeout=10)
        return "Telegram message sent."
    except Exception as e:
        return f"Telegram failed: {e}"

# ══════════════════════════════════════════════════════
#  MATH TOOLS
# ══════════════════════════════════════════════════════

def calculate(expression: str) -> str:
    """Safely evaluate a math expression."""
    try:
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "Invalid characters in expression."
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Calculation error: {e}"

def unit_convert(value: float, from_unit: str, to_unit: str) -> str:
    """Convert between common units."""
    v = float(value)
    conversions = {
        ("km",     "miles"):  v * 0.621371,
        ("miles",  "km"):     v * 1.60934,
        ("m",      "ft"):     v * 3.28084,
        ("ft",     "m"):      v * 0.3048,
        ("cm",     "inches"): v * 0.393701,
        ("inches", "cm"):     v * 2.54,
        ("kg",     "lbs"):    v * 2.20462,
        ("lbs",    "kg"):     v * 0.453592,
        ("g",      "oz"):     v * 0.035274,
        ("c",      "f"):      (v * 9/5) + 32,
        ("f",      "c"):      (v - 32) * 5/9,
        ("c",      "k"):      v + 273.15,
        ("gb",     "mb"):     v * 1024,
        ("mb",     "gb"):     v / 1024,
        ("tb",     "gb"):     v * 1024,
    }
    key    = (from_unit.lower(), to_unit.lower())
    result = conversions.get(key)
    if result is None:
        return f"Conversion {from_unit} to {to_unit} not supported."
    return f"{value} {from_unit} = {result:.4f} {to_unit}"

# ══════════════════════════════════════════════════════
#  MEMORY TOOLS
# ══════════════════════════════════════════════════════

def remember_fact(fact: str, category: str = "general") -> str:
    return remember(fact, category)

def recall_memory(query: str = "") -> str:
    return recall(query)

def forget_memory(query: str) -> str:
    return forget(query)

def save_preference(key: str, value: str) -> str:
    return set_preference(key, value)

def get_user_preference(key: str) -> str:
    return get_preference(key)

# ══════════════════════════════════════════════════════
#  TOOL REGISTRY
# ══════════════════════════════════════════════════════

TOOLS = {
    "search_web":        search_web,
    "open_website":      open_website,
    "fetch_webpage":     fetch_webpage,
    "summarize_url":     summarize_url,
    "open_app":          open_app,
    "close_app":         close_app,
    "run_command":       run_command,
    "get_datetime":      get_datetime,
    "get_system_info":   get_system_info,
    "get_battery":       get_battery,
    "get_disk_usage":    get_disk_usage,
    "get_processes":     get_running_processes,
    "kill_process":      kill_process,
    "take_screenshot":   take_screenshot,
    "copy_to_clipboard": copy_to_clipboard,
    "get_clipboard":     get_clipboard,
    "show_notification": show_notification,
    "set_reminder":      set_reminder,
    "start_timer":       start_timer,
    "read_file":         read_file,
    "write_file":        write_file,
    "append_file":       append_file,
    "delete_file":       delete_file,
    "copy_file":         copy_file,
    "move_file":         move_file,
    "list_files":        list_files,
    "open_file":         open_file,
    "create_folder":     create_folder,
    "rename_file":       rename_file,
    "zip_files":         zip_files,
    "read_csv":          read_csv,
    "analyze_csv":       analyze_csv,
    "read_excel":        read_excel,
    "csv_to_json":       csv_to_json,
    "read_json_file":    read_json_file,
    "write_csv":         write_csv,
    "run_python":        run_python,
    "run_script":        run_script,
    "install_package":   install_package,
    "create_note":       create_note,
    "list_notes":        list_notes,
    "read_note":         read_note,
    "append_note":       append_note,
    "delete_note":       delete_note,
    "search_notes":      search_notes,
    "open_note":         open_note,
    "send_whatsapp":     send_whatsapp,
    "whatsapp_web":      whatsapp_web,
    "draft_email":       draft_email,
    "share_via_browser": share_via_browser,
    "send_telegram":     send_telegram,
    "calculate":         calculate,
    "unit_convert":      unit_convert,
    "remember_fact":     remember_fact,
    "recall_memory":     recall_memory,
    "forget_memory":     forget_memory,
    "save_preference":   save_preference,
    "get_preference":    get_user_preference,
}

TOOL_DESCRIPTIONS = """
Available tools — call using: TOOL: tool_name(arg1="value1", arg2="value2")

WEB: search_web(query) | open_website(url) | fetch_webpage(url) | summarize_url(url)

APPS: open_app(app_name) | close_app(app_name)

SYSTEM: run_command(command) | get_datetime() | get_system_info() | get_battery()
        get_disk_usage() | get_processes() | kill_process(name) | take_screenshot(filename)
        copy_to_clipboard(text) | get_clipboard() | show_notification(title, message)
        set_reminder(message, seconds) | start_timer(seconds, label)

FILES: read_file(path) | write_file(path, content) | append_file(path, content)
       delete_file(path) | copy_file(src, dst) | move_file(src, dst) | list_files(directory)
       open_file(path) | create_folder(path) | rename_file(old_path, new_path) | zip_files(source, output)

DATA: read_csv(path, rows) | analyze_csv(path, query) | read_excel(path, sheet)
      csv_to_json(csv_path, json_path) | read_json_file(path) | write_csv(path, data)

CODE: run_python(code) | run_script(path) | install_package(package)

NOTES: create_note(title, content) | list_notes() | read_note(title) | append_note(title, content)
       delete_note(title) | search_notes(query) | open_note(title)

MESSAGING: send_whatsapp(phone, message) | whatsapp_web(phone, message)
           draft_email(to, subject, body) | share_via_browser(content, platform)
           send_telegram(message, bot_token, chat_id)

MATH: calculate(expression) | unit_convert(value, from_unit, to_unit)

MEMORY: remember_fact(fact, category) | recall_memory(query) | forget_memory(query)
        save_preference(key, value) | get_preference(key)

Chain tools for complex tasks:
- analyze_csv → whatsapp_web to send results
- search_web → create_note to save findings
- run_python → write_file to save output
"""

def execute_tool(tool_name: str, kwargs: dict) -> str:
    """Execute a tool by name with arguments."""
    func = TOOLS.get(tool_name)
    if not func:
        return f"Unknown tool: {tool_name}"
    try:
        return str(func(**kwargs))
    except TypeError as e:
        return f"Wrong arguments for {tool_name}: {e}"
    except Exception as e:
        return f"Tool error ({tool_name}): {e}"