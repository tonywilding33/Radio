import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk, filedialog

# Ensure script runs in its own directory
script_dir = os.path.dirname(os.path.abspath(__file__))
master_file = os.path.join(script_dir, "Playlist History.txt")
ini_file = os.path.join(script_dir, "PL.ini")

# Initialize Master File if it doesn't exist
if not os.path.exists(master_file):
    with open(master_file, "w", encoding="utf-8") as f:
        f.write("Timestamp|Artist|Song\n")

# Initialize INI File if it doesn't exist
if not os.path.exists(ini_file):
    with open(ini_file, "w", encoding="utf-8") as f:
        f.write(f"[Settings]\nLastImportPath={script_dir}\n")

# --- GUI SETUP ---
root = tk.Tk()
root.title("Playlist Tracker")
root.geometry("900x720")
root.resizable(False, False)

tabControl = ttk.Notebook(root)

# ==========================================
# TAB 1: IMPORT PLAYLIST
# ==========================================
tabImport = ttk.Frame(tabControl)
tabControl.add(tabImport, text="Import Playlist")

def browse_file():
    filename = filedialog.askopenfilename(
        initialdir=script_dir,
        title="Select Playlist File",
        filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
    )
    if filename:
        with open(filename, "r", encoding="utf-8") as f:
            txt_paste.delete("1.0", tk.END)
            txt_paste.insert(tk.END, f.read())

btn_browse = ttk.Button(tabImport, text="Browse Playlist File...", command=browse_file)
btn_browse.place(x=20, y=20, width=160, height=35)

lbl_paste = ttk.Label(tabImport, text="Or Paste Playlist Data (Format: Artist | Song  -or-  Artist - Song per line):")
lbl_paste.place(x=20, y=70)

txt_paste = tk.Text(tabImport, wrap=tk.WORD, width=102, height=24)
txt_paste.place(x=20, y=95)

def import_playlist():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = txt_paste.get("1.0", tk.END).strip()
    if not content:
        messagebox.showwarning("Warning", "Please paste or load playlist data first.")
        return

    records_to_add = []
    lines = content.splitlines()
    for l in lines:
        clean_line = l.strip()
        if not clean_line or clean_line.startswith("Timestamp"):
            continue
        artist, song = "", ""
        if "|" in clean_line:
            parts = clean_line.split("|")
            if len(parts) >= 2:
                artist = parts[0].strip()
                song = parts[1].strip()
        elif " - " in clean_line:
            parts = clean_line.split(" - ", 1)
            artist = parts[0].strip()
            song = parts[1].strip()
        else:
            continue

        if artist and song:
            records_to_add.append(f"{timestamp}|{artist}|{song}\n")

    if not records_to_add:
        messagebox.showwarning("Warning", "No valid entries found. Use 'Artist | Song' or 'Artist - Song'.")
        return

    with open(master_file, "a", encoding="utf-8") as f:
        f.writelines(records_to_add)

    txt_paste.delete("1.0", tk.END)
    messagebox.showinfo("Success", f"Successfully added {len(records_to_add)} play(s) to Playlist History.txt!")
    update_dropdowns()

btn_import = ttk.Button(tabImport, text="Add to Playlist History", command=import_playlist)
btn_import.place(x=20, y=530, width=220, height=40)


# ==========================================
# TAB 2: ANALYSIS & TOP 100
# ==========================================
tabAnalysis = ttk.Frame(tabControl)
tabControl.add(tabAnalysis, text="Analysis & Top 100")

def run_analysis():
    data = get_playlist_data()
    if not data:
        txt_analysis.delete("1.0", tk.END)
        txt_analysis.insert(tk.END, "No playlist history data found.")
        return

    counts = {}
    for row in data:
        key = (row["Artist"], row["Song"])
        counts[key] = counts.get(key, 0) + 1

    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    output = []
    output.append("=== PLAYLIST ANALYSIS REPORT ===")
    output.append(f"Generated: {datetime.now()}")
    output.append(f"Total Plays Logged: {len(data)}")
    output.append("-" * 80 + "\n[ SONG PLAY COUNTS BY ARTIST ]\n" + "-" * 80)

    for (artist, song), count in sorted_counts:
        output.append(f"Artist: {artist} | Song: {song} | Total Plays: {count}")

    output.append("\n" + "-" * 80 + "\n[ TOP 100 MOST PLAYED SONGS ]\n" + "-" * 80)

    top100 = sorted_counts[:100]
    for rank, ((artist, song), count) in enumerate(top100, 1):
        output.append(f"{rank:3d}. {artist} - '{song}' ({count} plays)")

    txt_analysis.delete("1.0", tk.END)
    txt_analysis.insert(tk.END, "\n".join(output))

btn_analyse = ttk.Button(tabAnalysis, text="Run Analysis", command=run_analysis)
btn_analyse.place(x=20, y=20, width=150, height=35)

txt_analysis = tk.Text(tabAnalysis, wrap=tk.WORD, width=102, height=26, font=("Courier", 10))
txt_analysis.place(x=20, y=70)


# ==========================================
# TAB 3: MONTHLY & YEARLY REPORTS
# ==========================================
tabReports = ttk.Frame(tabControl)
tabControl.add(tabReports, text="Monthly & Yearly Reports")

lbl_month = ttk.Label(tabReports, text="Select Month:")
lbl_month.place(x=20, y=18)

cmb_months = ttk.Combobox(tabReports, state="readonly", width=18)
cmb_months.place(x=110, y=15)

def gen_monthly():
    sel_month = cmb_months.get()
    if not sel_month:
        messagebox.showwarning("Warning", "Please select a month first.")
        return

    try:
        target_dt = datetime.strptime(sel_month, "%B %Y")
        target_prefix = target_dt.strftime("%Y-%m")
    except:
        return

    data = get_playlist_data()
    month_data = [row for row in data if row["Timestamp"].startswith(target_prefix)]

    if not month_data:
        txt_reports.delete("1.0", tk.END)
        txt_reports.insert(tk.END, f"No plays found for {sel_month}.")
        return

    counts = {}
    for row in month_data:
        key = (row["Artist"], row["Song"])
        counts[key] = counts.get(key, 0) + 1

    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    output = []
    output.append(f"=== MONTHLY PLAYLIST REPORT: {sel_month} ===")
    output.append("Format: Artist | Song | Number of Plays")
    output.append("-" * 80)

    for (artist, song), count in sorted_counts:
        output.append(f"{artist} | {song} | {count}")

    txt_reports.delete("1.0", tk.END)
    txt_reports.insert(tk.END, "\n".join(output))

btn_gen_monthly = ttk.Button(tabReports, text="Generate Monthly", command=gen_monthly)
btn_gen_monthly.place(x=270, y=12, width=130, height=28)

lbl_year = ttk.Label(tabReports, text="Select Year:")
lbl_year.place(x=430, y=18)

cmb_years = ttk.Combobox(tabReports, state="readonly", width=10)
cmb_years.place(x=510, y=15)

def gen_yearly():
    sel_year = cmb_years.get()
    if not sel_year:
        messagebox.showwarning("Warning", "Please select a year first.")
        return

    data = get_playlist_data()
    year_data = [row for row in data if row["Timestamp"].startswith(sel_year)]

    if not year_data:
        txt_reports.delete("1.0", tk.END)
        txt_reports.insert(tk.END, f"No play data found for the year {sel_year}.")
        return

    counts = {}
    for row in year_data:
        key = (row["Artist"], row["Song"])
        counts[key] = counts.get(key, 0) + 1

    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    output = []
    output.append(f"=== ANNUAL PLAYLIST REPORT: FULL YEAR {sel_year} ===")
    output.append(f"Total Plays Logged: {len(year_data)}")
    output.append("Format: Artist | Song | Number of Plays")
    output.append("-" * 80)

    for (artist, song), count in sorted_counts:
        output.append(f"{artist} | {song} | {count}")

    txt_reports.delete("1.0", tk.END)
    txt_reports.insert(tk.END, "\n".join(output))

btn_gen_yearly = ttk.Button(tabReports, text="Generate Yearly", command=gen_yearly)
btn_gen_yearly.place(x=620, y=12, width=130, height=28)

txt_reports = tk.Text(tabReports, wrap=tk.WORD, width=102, height=26, font=("Courier", 10))
txt_reports.place(x=20, y=55)


# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_playlist_data():
    if not os.path.exists(master_file):
        return []
    data = []
    with open(master_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if len(lines) <= 1:
            return []
        for line in lines[1:]:
            parts = line.strip().split("|")
            if len(parts) >= 3:
                data.append({"Timestamp": parts[0], "Artist": parts[1], "Song": parts[2]})
    return data

def update_dropdowns():
    data = get_playlist_data()
    if not data:
        return
    
    months_set = set()
    years_set = set()
    for row in data:
        ts = row["Timestamp"]
        if len(ts) >= 7:
            ym = ts[:7]
            try:
                dt = datetime.strptime(ym, "%Y-%m")
                months_set.add(dt.strftime("%B %Y"))
            except:
                pass
        if len(ts) >= 4:
            years_set.add(ts[:4])

    sorted_months = sorted(list(months_set), key=lambda x: datetime.strptime(x, "%B %Y"))
    sorted_years = sorted(list(years_set))

    cmb_months['values'] = sorted_months
    if sorted_months:
        cmb_months.set(sorted_months[0])

    cmb_years['values'] = sorted_years
    if sorted_years:
        cmb_years.set(sorted_years[0])

tabControl.pack(expand=1, fill="both", padx=10, pady=10)
update_dropdowns()

root.mainloop()