import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import platform
import subprocess
import json
import urllib.request
import urllib.parse
from datetime import datetime
from collections import defaultdict

# Determine base directory
if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))

master_file = os.path.join(script_dir, "Cumulative Requests.txt")

# Initialize Master File with headers if it doesn't exist
if not os.path.exists(master_file):
    with open(master_file, "w", encoding="utf-8") as f:
        f.write("Timestamp|Artist|Song|Year|Era|Genre|RequestType\n")

def get_uk_track_metadata(artist, song):
    try:
        query = f"{artist} {song}"
        encoded_term = urllib.parse.quote(query)
        url = f"https://itunes.apple.com/search?term={encoded_term}&entity=song&country=GB&limit=50"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        match = None
        if data.get("resultCount", 0) > 0:
            results = data.get("results", [])
            valid_matches = [
                r for r in results 
                if artist.lower() in r.get("artistName", "").lower() 
                and "live" not in r.get("trackName", "").lower()
                and "live" not in r.get("collectionName", "").lower()
            ]
            if not valid_matches:
                valid_matches = [r for r in results if "live" not in r.get("trackName", "").lower()]
            if not valid_matches:
                valid_matches = results
            
            valid_matches.sort(key=lambda x: x.get("releaseDate", "9999"))
            match = valid_matches[0] if valid_matches else None
        else:
            encoded_song = urllib.parse.quote(song)
            fallback_url = f"https://itunes.apple.com/search?term={encoded_song}&entity=song&country=GB&limit=50"
            req_fb = urllib.request.Request(fallback_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_fb, timeout=10) as response:
                fallback_data = json.loads(response.read().decode('utf-8'))
            if fallback_data.get("resultCount", 0) > 0:
                results = fallback_data.get("results", [])
                valid_matches = [r for r in results if "live" not in r.get("trackName", "").lower()]
                if not valid_matches:
                    valid_matches = results
                valid_matches.sort(key=lambda x: x.get("releaseDate", "9999"))
                match = valid_matches[0] if valid_matches else None

        if match:
            release_date = match.get("releaseDate", "")
            release_year = release_date[:4] if release_date else ""
            era = f"{(int(release_year) // 10) * 10}s" if release_year.isdigit() else "2020s"
            genre = match.get("primaryGenreName", "Pop")
            return {
                "Success": True,
                "Year": release_year,
                "Era": era,
                "Genre": genre,
                "Title": match.get("trackName", ""),
                "Artist": match.get("artistName", ""),
                "Album": match.get("collectionName", "")
            }
    except Exception:
        pass
    return {"Success": False}

def load_request_data():
    if not os.path.exists(master_file):
        return []
    records = []
    with open(master_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if not lines:
        return []
    header = [h.strip() for h in lines[0].split("|")]
    for line in lines[1:]:
        parts = [p.strip() for p in line.strip().split("|")]
        if len(parts) >= len(header):
            records.append(dict(zip(header, parts)))
        elif len(parts) >= 2:
            rec = {
                "Timestamp": parts[0],
                "Artist": parts[1],
                "Song": parts[2] if len(parts) > 2 else "",
                "Year": "",
                "Era": "2020s",
                "Genre": "Pop",
                "RequestType": "Patient Request"
            }
            records.append(rec)
    return records

# Main App Window Setup
root = tk.Tk()
root.title("Request Data Tracker with Preview (Cross-Platform)")
root.geometry("900x740")
root.resizable(False, False)

tabControl = ttk.Notebook(root)
tabControl.pack(fill="both", expand=True, padx=10, pady=10)

# ==========================================
# TAB 1: ADD REQUESTS, QUEUE & PREVIEW
# ==========================================
tabAdd = ttk.Frame(tabControl)
tabControl.add(tabAdd, text="Add Requests & Queue")

tk.Label(tabAdd, text="Artist:").place(x=20, y=20)
txtArtist = ttk.Entry(tabAdd, width=35)
txtArtist.place(x=120, y=18)

tk.Label(tabAdd, text="Song:").place(x=20, y=60)
txtSong = ttk.Entry(tabAdd, width=35)
txtSong.place(x=120, y=58)

def fetch_meta_single():
    artist = txtArtist.get().strip()
    song = txtSong.get().strip()
    if not artist or not song:
        messagebox.showwarning("Missing Info", "Please enter both Artist and Song before fetching metadata.")
        return
    root.config(cursor="watch")
    root.update()
    res = get_uk_track_metadata(artist, song)
    root.config(cursor="")
    if res["Success"]:
        txtYear.delete(0, tk.END)
        txtYear.insert(0, res["Year"])
        txtEra.delete(0, tk.END)
        txtEra.insert(0, res["Era"])
        txtGenre.delete(0, tk.END)
        txtGenre.insert(0, res["Genre"])
        messagebox.showinfo("Metadata Found", f"Successfully fetched UK metadata!\nFound: {res['Artist']} - {res['Title']}\nRelease Year: {res['Year']}\nAlbum: {res['Album']}\nGenre: {res['Genre']} | Era: {res['Era']}")
    else:
        messagebox.showinfo("Not Found", "Could not automatically locate track data in the UK store. Please fill in manually.")

btnFetchMeta = ttk.Button(tabAdd, text="Auto-Fetch UK Details", command=fetch_meta_single)
btnFetchMeta.place(x=380, y=56, width=140, height=26)

def add_to_queue():
    artist = txtArtist.get().strip()
    song = txtSong.get().strip()
    if not artist or not song:
        messagebox.showwarning("Missing Info", "Please enter both Artist and Song to add to the queue.")
        return
    queue_line = f"{artist} | {song}"
    current_text = txtPaste.get("1.0", tk.END).strip()
    if current_text:
        txtPaste.insert(tk.END, f"\n{queue_line}")
    else:
        txtPaste.delete("1.0", tk.END)
        txtPaste.insert("1.0", queue_line)
    txtArtist.delete(0, tk.END)
    txtSong.delete(0, tk.END)
    txtYear.delete(0, tk.END)
    txtArtist.focus()

btnAddToQueue = ttk.Button(tabAdd, text="Add to Queue ->", command=add_to_queue)
btnAddToQueue.place(x=530, y=56, width=140, height=26)

tk.Label(tabAdd, text="Release Year:").place(x=20, y=100)
txtYear = ttk.Entry(tabAdd, width=35)
txtYear.place(x=120, y=98)

tk.Label(tabAdd, text="Era (Decade):").place(x=20, y=140)
txtEra = ttk.Entry(tabAdd, width=35)
txtEra.insert(0, "2020s")
txtEra.place(x=120, y=138)

tk.Label(tabAdd, text="Genre:").place(x=20, y=180)
txtGenre = ttk.Entry(tabAdd, width=35)
txtGenre.place(x=120, y=178)

tk.Label(tabAdd, text="Request Type:").place(x=20, y=220)
cmbType = ttk.Combobox(tabAdd, values=["Patient Request", "Filler"], state="readonly", width=33)
cmbType.set("Patient Request")
cmbType.place(x=120, y=218)

def browse_file():
    filename = filedialog.askopenfilename(initialdir=script_dir, title="Select Text File", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    if filename:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        txtPaste.delete("1.0", tk.END)
        txtPaste.insert("1.0", content)

btnBrowse = ttk.Button(tabAdd, text="Load Text File...", command=browse_file)
btnBrowse.place(x=680, y=54, width=160, height=28)

tk.Label(tabAdd, text="Queue / Bulk Paste Window (Format: Artist | Song):").place(x=20, y=255)

txtPaste = tk.Text(tabAdd, width=102, height=12, wrap="word")
txtPaste.place(x=20, y=280)

def preview_metadata():
    content = txtPaste.get("1.0", tk.END).strip()
    if not content:
        messagebox.showwarning("Warning", "The queue/paste window is empty. Please add items or paste a list first.")
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    request_type = cmbType.get()
    preview_lines = []
    lines = content.splitlines()

    root.config(cursor="watch")
    root.update()

    for l in lines:
        clean_line = l.strip()
        if clean_line and not clean_line.startswith("Timestamp"):
            parts = [p.strip() for p in clean_line.split("|")]
            if len(parts) >= 7:
                preview_lines.append(clean_line)
                continue
            if len(parts) >= 2:
                art, sng = parts[0], parts[1]
                meta = get_uk_track_metadata(art, sng)
                yr = meta["Year"] if meta["Success"] else txtYear.get().strip()
                er = meta["Era"] if meta["Success"] else txtEra.get().strip()
                gn = meta["Genre"] if meta["Success"] else txtGenre.get().strip()
                preview_lines.append(f"{timestamp}|{art}|{sng}|{yr}|{er}|{gn}|{request_type}")

    root.config(cursor="")

    if not preview_lines:
        messagebox.showwarning("Warning", "No valid records could be parsed from the queue window.")
        return

    txtPaste.delete("1.0", tk.END)
    txtPaste.insert("1.0", "\n".join(preview_lines))
    messagebox.showinfo("Preview Ready", "Preview generated successfully! Review the enriched data in the box above, then click 'Confirm & Save to History' when ready.")

btnPreview = ttk.Button(tabAdd, text="1. Fetch & Preview Metadata", command=preview_metadata)
btnPreview.place(x=20, y=490, width=240, height=35)

def confirm_save():
    content = txtPaste.get("1.0", tk.END).strip()
    if not content:
        messagebox.showwarning("Warning", "No previewed data found in the window to save.")
        return

    lines = content.splitlines()
    records_to_save = []
    for l in lines:
        clean_line = l.strip()
        if clean_line and not clean_line.startswith("Timestamp"):
            parts = [p.strip() for p in clean_line.split("|")]
            if len(parts) >= 7:
                records_to_save.append(clean_line)
            elif len(parts) >= 2:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                request_type = cmbType.get()
                records_to_save.append(f"{timestamp}|{parts[0]}|{parts[1]}||2020s|Pop|{request_type}")

    if not records_to_save:
        messagebox.showwarning("Warning", "No valid records found to save.")
        return

    with open(master_file, "a", encoding="utf-8") as f:
        for rec in records_to_save:
            f.write(rec + "\n")

    txtArtist.delete(0, tk.END)
    txtSong.delete(0, tk.END)
    txtYear.delete(0, tk.END)
    txtPaste.delete("1.0", tk.END)

    messagebox.showinfo("Success", f"Successfully saved {len(records_to_save)} record(s) to the cumulative history file!")
    update_dropdowns()

btnCommit = ttk.Button(tabAdd, text="2. Confirm & Save to History", command=confirm_save)
btnCommit.place(x=275, y=490, width=240, height=35)


# ==========================================
# TAB 2: ANALYSIS & TOP 100
# ==========================================
tabAnalysis = ttk.Frame(tabControl)
tabControl.add(tabAnalysis, text="Analysis & Top 100")

def run_analysis():
    data = load_request_data()
    if not data:
        txtAnalysisOutput.delete("1.0", tk.END)
        txtAnalysisOutput.insert("1.0", "No request data found in master file.")
        return

    counts = defaultdict(lambda: {"count": 0, "sample": None})
    for row in data:
        key = (row.get("Artist", "").strip(), row.get("Song", "").strip())
        counts[key]["count"] += 1
        if not counts[key]["sample"]:
            counts[key]["sample"] = row

    sorted_songs = sorted(counts.items(), key=lambda x: x[1]["count"], reverse=True)

    sb = []
    sb.append("=== REQUEST ANALYSIS REPORT ===")
    sb.append(f"Generated: {datetime.now()}")
    sb.append(f"Total Cumulative Items Logged: {len(data)}")
    sb.append("-" * 80)
    sb.append("")
    sb.append("[ SONG REQUEST COUNTS BY ARTIST ]")

    for (art, sng), info in sorted_songs:
        sample = info["sample"]
        sb.append(f"Artist: {art} | Song: {sng} | Requests: {info['count']} | Year: {sample.get('Year','')} | Era: {sample.get('Era','')} | Genre: {sample.get('Genre','')} | Type: {sample.get('RequestType','')}")

    sb.append("")
    sb.append("-" * 80)
    sb.append("[ TOP 100 REQUESTS BY ARTIST AND SONG ]")
    sb.append("-" * 80)

    top100 = sorted_songs[:100]
    for rank, ((art, sng), info) in enumerate(top100, start=1):
        sb.append(f"{rank:3d}. {art} - '{sng}' ({info['count']} requests)")

    txtAnalysisOutput.delete("1.0", tk.END)
    txtAnalysisOutput.insert("1.0", "\n".join(sb))

btnAnalyse = ttk.Button(tabAnalysis, text="Run Analysis", command=run_analysis)
btnAnalyse.place(x=20, y=20, width=150, height=35)

txtAnalysisOutput = tk.Text(tabAnalysis, width=102, height=33, wrap="word", font=("Consolas", 10))
txtAnalysisOutput.place(x=20, y=70)


# ==========================================
# TAB 3: MONTHLY & YEARLY REPORTS
# ==========================================
tabReports = ttk.Frame(tabControl)
tabControl.add(tabReports, text="Monthly & Yearly Reports")

tk.Label(tabReports, text="Select Month:").place(x=20, y=18)
cmbMonths = ttk.Combobox(tabReports, state="readonly", width=18)
cmbMonths.place(x=110, y=15)

def generate_monthly():
    sel_month = cmbMonths.get()
    if not sel_month:
        messagebox.showwarning("Warning", "Please select a month first.")
        return
    
    try:
        target_date = datetime.strptime(sel_month, "%B %Y")
        target_prefix = target_date.strftime("%Y-%m")
    except Exception:
        return

    data = load_request_data()
    month_data = [r for r in data if r.get("Timestamp", "").startswith(target_prefix)]

    if not month_data:
        txtReportOutput.delete("1.0", tk.END)
        txtReportOutput.insert("1.0", f"No requests found for {sel_month}.")
        return

    counts = defaultdict(lambda: {"count": 0, "sample": None})
    for row in month_data:
        key = (row.get("Artist", "").strip(), row.get("Song", "").strip())
        counts[key]["count"] += 1
        if not counts[key]["sample"]:
            counts[key]["sample"] = row

    sorted_m = sorted(counts.items(), key=lambda x: x[1]["count"], reverse=True)

    sb = []
    sb.append(f"=== MONTHLY REPORT: {sel_month} ===")
    sb.append("Format: Artist | Song | Number of Requests | Year | Era | Genre | Type")
    sb.append("-" * 80)

    for (art, sng), info in sorted_m:
        sample = info["sample"]
        sb.append(f"{art} | {sng} | {info['count']} | Year: {sample.get('Year','')} | Era: {sample.get('Era','')} | Genre: {sample.get('Genre','')} | Type: {sample.get('RequestType','')}")

    txtReportOutput.delete("1.0", tk.END)
    txtReportOutput.insert("1.0", "\n".join(sb))

btnGenMonthly = ttk.Button(tabReports, text="Generate Monthly", command=generate_monthly)
btnGenMonthly.place(x=270, y=12, width=130, height=28)

tk.Label(tabReports, text="Select Year:").place(x=430, y=18)
cmbYears = ttk.Combobox(tabReports, state="readonly", width=12)
cmbYears.place(x=510, y=15)

def generate_yearly():
    sel_year = cmbYears.get()
    if not sel_year:
        messagebox.showwarning("Warning", "Please select a year first.")
        return

    data = load_request_data()
    year_data = [r for r in data if r.get("Timestamp", "").startswith(sel_year)]

    if not year_data:
        txtReportOutput.delete("1.0", tk.END)
        txtReportOutput.insert("1.0", f"No request or filler data found for the year {sel_year}.")
        return

    counts = defaultdict(lambda: {"count": 0, "sample": None})
    for row in year_data:
        key = (row.get("Artist", "").strip(), row.get("Song", "").strip())
        counts[key]["count"] += 1
        if not counts[key]["sample"]:
            counts[key]["sample"] = row

    sorted_y = sorted(counts.items(), key=lambda x: x[1]["count"], reverse=True)

    sb = []
    sb.append(f"=== ANNUAL REPORT: FULL YEAR {sel_year} ===")
    sb.append(f"Total Plays Logged: {len(year_data)}")
    sb.append("Format: Artist | Song | Number of Requests | Year | Era | Genre | Type")
    sb.append("-" * 80)

    for (art, sng), info in sorted_y:
        sample = info["sample"]
        sb.append(f"{art} | {sng} | {info['count']} | Year: {sample.get('Year','')} | Era: {sample.get('Era','')} | Genre: {sample.get('Genre','')} | Type: {sample.get('RequestType','')}")

    txtReportOutput.delete("1.0", tk.END)
    txtReportOutput.insert("1.0", "\n".join(sb))

btnGenYearly = ttk.Button(tabReports, text="Generate Yearly", command=generate_yearly)
btnGenYearly.place(x=620, y=12, width=130, height=28)

txtReportOutput = tk.Text(tabReports, width=102, height=33, wrap="word", font=("Consolas", 10))
txtReportOutput.place(x=20, y=55)


# ==========================================
# TAB 4: SETTINGS (CROSS-PLATFORM NETWORK)
# ==========================================
tabSettings = ttk.Frame(tabControl)
tabControl.add(tabSettings, text="Settings")

grpNetwork = ttk.LabelFrame(tabSettings, text="Network & Wi-Fi Scanner & Connector")
grpNetwork.place(x=20, y=20, width=825, height=600)

def scan_networks():
    root.config(cursor="watch")
    root.update()
    txtNetStatus.delete("1.0", tk.END)
    listNetworks.delete(0, tk.END)

    sb = []
    sb.append("=== Active System & Network Info ===")
    sb.append(f"OS Platform: {platform.system()} {platform.release()}")
    
    try:
        current_os = platform.system()
        if current_os == "Windows":
            res = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=5)
            sb.append(res.stdout)
            
            res_nets = subprocess.run(["netsh", "wlan", "show", "networks"], capture_output=True, text=True, timeout=5)
            for line in res_nets.stdout.splitlines():
                if "SSID" in line and ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        ssid = parts[1].strip()
                        if ssid and ssid not in listNetworks.get(0, tk.END):
                            listNetworks.insert(tk.END, ssid)
        elif current_os == "Darwin":
            res = subprocess.run(["networksetup", "-listallhardwareports"], capture_output=True, text=True, timeout=5)
            sb.append(res.stdout)
            airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
            if os.path.exists(airport_path):
                res_wifi = subprocess.run([airport_path, "-s"], capture_output=True, text=True, timeout=5)
                sb.append("\nAvailable Wi-Fi Networks:")
                sb.append(res_wifi.stdout)
                for line in res_wifi.stdout.splitlines()[1:]:
                    parts = line.strip().split()
                    if parts:
                        ssid = parts[0]
                        if ssid not in listNetworks.get(0, tk.END):
                            listNetworks.insert(tk.END, ssid)
        elif current_os == "Linux":
            res = subprocess.run(["nmcli", "device", "wifi", "list"], capture_output=True, text=True, timeout=5)
            sb.append(res.stdout)
            for line in res.stdout.splitlines()[1:]:
                parts = line.split()
                if len(parts) > 1:
                    ssid = parts[1]
                    if ssid and ssid not in listNetworks.get(0, tk.END):
                        listNetworks.insert(tk.END, ssid)
    except Exception as e:
        sb.append(f"Could not retrieve live Wi-Fi scan: {str(e)}")

    txtNetStatus.insert("1.0", "\n".join(sb))
    root.config(cursor="")

btnScanNet = ttk.Button(grpNetwork, text="Clear & Rescan Available Networks", command=scan_networks)
btnScanNet.place(x=20, y=30, width=350, height=30)

txtNetStatus = tk.Text(grpNetwork, width=42, height=6, wrap="word")
txtNetStatus.place(x=20, y=75)
txtNetStatus.insert("1.0", "Click 'Clear & Rescan' to fetch fresh networks.")

tk.Label(grpNetwork, text="Available Networks (Fresh Scan Only):").place(x=20, y=185)

listNetworks = tk.Listbox(grpNetwork, width=42, height=8)
listNetworks.place(x=20, y=210)

tk.Label(grpNetwork, text="Network Username:").place(x=400, y=32)
txtWifiUser = ttk.Entry(grpNetwork, width=30)
txtWifiUser.place(x=540, y=30)

tk.Label(grpNetwork, text="Network Password:").place(x=400, y=72)
txtWifiPwd = ttk.Entry(grpNetwork, width=30, show="*")
txtWifiPwd.place(x=540, y=70)

def connect_network():
    selected_indices = listNetworks.curselection()
    if not selected_indices:
        messagebox.showwarning("No Network Selected", "Please select an available network from the list first.")
        return
    selected_ssid = listNetworks.get(selected_indices[0])
    net_user = txtWifiUser.get().strip()
    net_pwd = txtWifiPwd.get()

    txtNetStatus.delete("1.0", tk.END)
    txtNetStatus.insert("1.0", f"Initiating connection to '{selected_ssid}'...")
    root.update()

    try:
        current_os = platform.system()
        if current_os == "Windows":
            pass
        elif current_os == "Darwin":
            subprocess.run(["networksetup", "-setairportnetwork", "en0", selected_ssid, net_pwd], capture_output=True, text=True, timeout=10)
        elif current_os == "Linux":
            subprocess.run(["nmcli", "device", "wifi", "connect", selected_ssid, "password", net_pwd], capture_output=True, text=True, timeout=10)
        messagebox.showinfo("Connection Attempt", f"Attempted connection to {selected_ssid}.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to connect: {str(e)}")

btnConnectNet = ttk.Button(grpNetwork, text="Connect to Selected Network", command=connect_network)
btnConnectNet.place(x=400, y=120, width=390, height=35)

def disconnect_network():
    try:
        current_os = platform.system()
        if current_os == "Windows":
            subprocess.run(["netsh", "wlan", "disconnect"], capture_output=True, text=True)
        elif current_os == "Darwin":
            subprocess.run(["networksetup", "-setairportpower", "en0", "off"], capture_output=True, text=True)
            subprocess.run(["networksetup", "-setairportpower", "en0", "on"], capture_output=True, text=True)
        elif current_os == "Linux":
            subprocess.run(["nmcli", "networking", "off"], capture_output=True, text=True)
            subprocess.run(["nmcli", "networking", "on"], capture_output=True, text=True)
        messagebox.showinfo("Disconnected", "Successfully disconnected from wireless network.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to disconnect: {str(e)}")

btnDisconnectNet = ttk.Button(grpNetwork, text="Disconnect from Current Network", command=disconnect_network)
btnDisconnectNet.place(x=400, y=170, width=390, height=35)


def update_dropdowns():
    data = load_request_data()
    if not data:
        return
    
    months_set = set()
    years_set = set()
    for row in data:
        ts = row.get("Timestamp", "")
        if len(ts) >= 7 and ts[:4].isdigit():
            y_str = ts[:4]
            years_set.add(y_str)
            try:
                dt = datetime.strptime(ts[:7], "%Y-%m")
                months_set.add(dt.strftime("%B %Y"))
            except Exception:
                pass

    sorted_months = sorted(list(months_set), key=lambda x: datetime.strptime(x, "%B %Y"))
    cmbMonths["values"] = sorted_months
    if sorted_months:
        cmbMonths.set(sorted_months[0])

    sorted_years = sorted(list(years_set))
    cmbYears["values"] = sorted_years
    if sorted_years:
        cmbYears.set(sorted_years[0])

update_dropdowns()

root.mainloop()