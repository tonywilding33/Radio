from datetime import datetime
import json
import os
import configparser
import flet as ft
import requests

# --- CONFIGURATION & CONSTANTS ---
CONFIG_FILE = "ward_collector.ini"
GITHUB_UAC_URL = (
    "https://raw.githubusercontent.com/tonywilding33/Radio/refs/heads/main/UAC.txt"
)
GITHUB_DB_URL = (
    "https://raw.githubusercontent.com/tonywilding33/Radio/refs/heads/main/rugbyhr.txt"
)


def main(page: ft.Page):
  page.title = "Ward Visitor Request Collector"
  page.vertical_alignment = ft.MainAxisAlignment.START
  page.padding = 20
  page.theme_mode = ft.ThemeMode.LIGHT
  page.scroll = ft.ScrollMode.AUTO

  # Local session memory for recalled requests
  session_requests = []

  # --- INI CONFIGURATION MANAGEMENT ---
  config = configparser.ConfigParser()

  def load_settings():
    if os.path.exists(CONFIG_FILE):
      config.read(CONFIG_FILE)
      return {
          "username": config.get("Credentials", "UserName", fallback=""),
          "secretword": config.get("Credentials", "SecretWord", fallback=""),
          "serial": config.get("Credentials", "Serial", fallback=""),
          "printer_ip": config.get(
              "Printer", "PrinterIP", fallback="192.168.1.100"
          ),
      }
    return {
        "username": "",
        "secretword": "",
        "serial": "",
        "printer_ip": "192.168.1.100",
    }

  def save_settings(username, secretword, serial, printer_ip):
    config["Credentials"] = {
        "UserName": username,
        "SecretWord": secretword,
        "Serial": serial,
    }
    config["Printer"] = {"PrinterIP": printer_ip}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
      config.write(f)

  settings = load_settings()

  # --- UAC GATEWAY & DATABASE QUERY LOGIC ---
  def verify_uac_gateway(username, secretword, serial):
    if not username:
      return False, "No Assigned Name entered."
    try:
      response = requests.get(GITHUB_UAC_URL, timeout=10)
      if response.status_code != 200:
        return False, "Failed to connect to UAC gateway."

      lines = response.text.splitlines()
      for line in lines:
        if not line.strip():
          continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 4:
          db_name, db_word, db_serial, db_access = (
              parts[0],
              parts[1],
              parts[2],
              parts[3],
          ]
          if db_name == username and "Granted" in db_access:
            if (not secretword or db_word == secretword) and (
                not serial or db_serial == serial
            ):
              return True, f"Access Granted for {username}."
      return (
          False,
          "Access Denied: Credentials not found or access revoked.",
      )
    except Exception as e:
      return False, f"Gateway Error: {str(e)}"

  def query_online_database(artist_query, song_query):
    # Authenticate first using cached settings
    is_auth, msg = verify_uac_gateway(
        settings["username"], settings["secretword"], settings["serial"]
    )
    if not is_auth:
      return False, f"Authentication Failed: {msg}"

    try:
      res = requests.get(GITHUB_DB_URL, timeout=12)
      if res.status_code != 200:
        return False, "Error connecting to remote library database."

      lines = res.text.splitlines()
      artist_tokens = artist_query.strip().split()
      song_tokens = song_query.strip().split()

      found = False
      for line in lines:
        if not line.strip():
          continue
        cols = (
            line.split("\t")
            if "\t" in line
            else (line.split(";") if ";" in line else line.split(","))
        )
        cleaned = [c.strip(' "') for c in cols]

        if len(cleaned) >= 4:
          if cleaned[0] == "Source":
            continue
          artist_field = cleaned[2]
          song_field = cleaned[3]

          match_artist = all(
              t.lower() in artist_field.lower() for t in artist_tokens
          )
          match_song = all(t.lower() in song_field.lower() for t in song_tokens)

          if match_artist and match_song:
            found = True
            break

      if found:
        return (
            True,
            "SUCCESS: Track is available in the library database! No"
            " alternative needed.",
        )
      else:
        return (
            False,
            "NOT FOUND: Track is unavailable. Please ask the patient for an"
            " alternative request.",
        )
    except Exception as e:
      return False, f"Query Exception: {str(e)}"

  # --- UI COMPONENTS: TAB 1 (REQUEST ENTRY FORM) ---
  today_str = datetime.now().strftime("%d_%m_%y")

  txt_date = ft.TextField(
      label="Date (dd_mm_yy)", value=today_str, width=200
  )
  txt_ward = ft.TextField(label="Ward", width=250)
  txt_patient = ft.TextField(label="Patient Name", width=300)
  txt_collector = ft.TextField(
      label="Request Collector (Visitor Name)",
      value=settings["username"],
      width=300,
  )
  txt_artist = ft.TextField(label="Artist Name", width=300)
  txt_song = ft.TextField(label="Song Title", width=300)
  txt_alternative = ft.TextField(
      label="Alternative Request (Title & Artist)", width=300
  )

  lbl_query_status = ft.Text("", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)

  recall_list_view = ft.ListView(expand=1, spacing=10, padding=10, auto_scroll=True)

  def on_query_click(e):
    if not txt_artist.value or not txt_song.value:
      lbl_query_status.value = (
          "Please enter both Artist and Song Title to query."
      )
      lbl_query_status.color = ft.Colors.RED
      page.update()
      return

    lbl_query_status.value = "Querying library database..."
    lbl_query_status.color = ft.Colors.ORANGE
    page.update()

    available, msg = query_online_database(txt_artist.value, txt_song.value)
    lbl_query_status.value = msg
    lbl_query_status.color = ft.Colors.GREEN if available else ft.Colors.RED
    page.update()

  def on_save_click(e):
    if not txt_patient.value or not txt_song.value:
      page.open(
          ft.SnackBar(
              ft.Text(
                  "Patient Name and Song Title are required fields."
              ),
              bgcolor=ft.Colors.RED,
          )
      )
      return

    record = {
        "date": txt_date.value,
        "ward": txt_ward.value,
        "patient": txt_patient.value,
        "collector": txt_collector.value,
        "artist": txt_artist.value,
        "song": txt_song.value,
        "alternative": txt_alternative.value,
    }

    session_requests.append(record)

    # Update Studio Recall List View UI
    recall_list_view.controls.append(
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        f"Ward: {record['ward']} | Patient:"
                        f" {record['patient']}",
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        f"Request: {record['artist']} - {record['song']}"
                    ),
                    ft.Text(
                        f"Alternative: {record['alternative'] or 'None'}",
                        italic=True,
                    ),
                    ft.Text(
                        f"Collector: {record['collector']} ({record['date']})",
                        size=12,
                        color=ft.Colors.GREY_700,
                    ),
                ]),
                padding=10,
            )
        )
    )

    # Clear form for next patient (keep date/ward/collector for convenience)
    txt_patient.value = ""
    txt_artist.value = ""
    txt_song.value = ""
    txt_alternative.value = ""
    lbl_query_status.value = (
        "Request saved successfully! Form ready for next patient."
    )
    lbl_query_status.color = ft.Colors.GREEN
    page.update()

  btn_query = ft.ElevatedButton(
      "Query Library Availability",
      icon=ft.Icons.SEARCH,
      on_click=on_query_click,
  )
  btn_save = ft.ElevatedButton(
      "Save Request & Next Patient",
      icon=ft.Icons.SAVE,
      bgcolor=ft.Colors.GREEN,
      color=ft.Colors.WHITE,
      on_click=on_save_click,
  )

  form_tab = ft.Tab(
      text="Patient Request Form",
      content=ft.Column([
          ft.Row([txt_date, txt_ward], spacing=20),
          ft.Row([txt_patient, txt_collector], spacing=20),
          ft.Divider(),
          ft.Row([txt_artist, txt_song], spacing=20),
          txt_alternative,
          ft.Row([btn_query, btn_save], spacing=20),
          lbl_query_status,
      ], spacing=15),
  )

  # --- UI COMPONENTS: TAB 2 (STUDIO RECALL & EXPORTS) ---
  def generate_export_files(e):
    if not session_requests:
      page.open(
          ft.SnackBar(
              ft.Text("No requests recorded in this session."),
              bgcolor=ft.Colors.ORANGE,
          )
      )
      return

    date_tag = today_str

    # 1. Central Transfer File (ANONYMIZED: Omit Patient Name & Ward for Data Protection)
    central_filename = f"Requests_{date_tag}.txt"
    with open(central_filename, "w", encoding="utf-8") as f:
      f.write("Timestamp | Artist | Song | Alternative | Collector\n")
      for req in session_requests:
        f.write(
            f"{req['date']} | {req['artist']} | {req['song']} |"
            f" {req['alternative']} | {req['collector']}\n"
        )

    # 2. Full Daily Report File (Includes complete visitor tracking stats)
    report_filename = f"Request Data_{date_tag}.txt"
    with open(report_filename, "w", encoding="utf-8") as f:
      f.write(f"=== WARD VISITOR DAILY REPORT ({date_tag}) ===\n\n")
      for i, req in enumerate(session_requests, 1):
        f.write(
            f"[{i}] Date: {req['date']} | Ward: {req['ward']} | Patient:"
            f" {req['patient']}\n"
        )
        f.write(
            f"    Song: {req['artist']} - {req['song']} (Alt:"
            f" {req['alternative']})\n"
        )
        f.write(f"    Collector: {req['collector']}\n\n")

    page.open(
        ft.SnackBar(
            ft.Text(
                f"Successfully generated files: {central_filename} and"
                f" {report_filename}"
            ),
            bgcolor=ft.Colors.GREEN,
        )
    )

  btn_export = ft.ElevatedButton(
      "Generate Central Transfer & Daily Report Files",
      icon=ft.Icons.FILE_DOWNLOAD,
      on_click=generate_export_files,
  )

  studio_tab = ft.Tab(
      text="Studio Recall & Export",
      content=ft.Column([
          ft.Text(
              "Recalled Requests List (For Studio Coordination):",
              weight=ft.FontWeight.BOLD,
          ),
          recall_list_view,
          ft.Divider(),
          btn_export,
      ], expand=True, spacing=10),
  )

  # --- UI COMPONENTS: TAB 3 (SETTINGS & PRINTER CONFIG) ---
  txt_set_user = ft.TextField(
      label="Assigned Name", value=settings["username"], width=300
  )
  txt_set_word = ft.TextField(
      label="Secret Word",
      value=settings["secretword"],
      password=True,
      width=300,
  )
  txt_set_serial = ft.TextField(
      label="Serial Code", value=settings["serial"], width=300
  )
  txt_printer_ip = ft.TextField(
      label="Wi-Fi Printer IP / Address",
      value=settings["printer_ip"],
      width=300,
  )

  def on_save_settings(e):
    save_settings(
        txt_set_user.value,
        txt_set_word.value,
        txt_set_serial.value,
        txt_printer_ip.value,
    )
    settings.update(load_settings())
    txt_collector.value = settings["username"]
    page.open(
        ft.SnackBar(
            ft.Text("Settings and printer configuration saved successfully."),
            bgcolor=ft.Colors.GREEN,
        )
    )

  btn_save_settings = ft.ElevatedButton(
      "Save Settings to INI", icon=ft.Icons.SETTINGS, on_click=on_save_settings
  )

  settings_tab = ft.Tab(
      text="Settings",
      content=ft.Column([
          ft.Text(
              "Gateway UAC Credentials & Wi-Fi Printer Configuration",
              weight=ft.FontWeight.BOLD,
          ),
          txt_set_user,
          txt_set_word,
          txt_set_serial,
          txt_printer_ip,
          btn_save_settings,
      ], spacing=15),
  )

  # Add Tabs to Page
  page.add(
      ft.Tabs(
          selected_index=0,
          animation_duration=300,
          tabs=[form_tab, studio_tab, settings_tab],
          expand=1,
      )
  )


ft.app(target=main)
