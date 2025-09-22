#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# RRA Backup Tool for Cacti
# Safely exports RRD files to XML, compresses them, and saves to local backup folder.

import os
import subprocess
import datetime
import shutil

# === CONFIGURATION ===
RRA_DIR = "/var/lib/cacti/rra"      # where your .rrd files live
LOCAL_BACKUP_DIR = "/opt/cacti_backups"  # where final .tar.gz will be stored
TMP_EXPORT_DIR = "/tmp/rra_xml"     # temp folder for XML dumps

def stop_cron():
    print("🛑 Stopping cron (poller)...")
    subprocess.run(["systemctl", "stop", "cron"], check=False)

def start_cron():
    print("▶️ Restarting cron (poller)...")
    subprocess.run(["systemctl", "start", "cron"], check=False)

def export_rrds():
    print("📤 Exporting RRDs to XML...")
    os.makedirs(TMP_EXPORT_DIR, exist_ok=True)

    for root, _, files in os.walk(RRA_DIR):
        for f in files:
            if f.endswith(".rrd"):
                rrd_path = os.path.join(root, f)
                xml_name = os.path.relpath(rrd_path, RRA_DIR).replace("/", "_") + ".xml"
                xml_path = os.path.join(TMP_EXPORT_DIR, xml_name)
                subprocess.run(["rrdtool", "dump", rrd_path, xml_path])
    print(f"✅ Export complete → {TMP_EXPORT_DIR}")

def compress_export():
    os.makedirs(LOCAL_BACKUP_DIR, exist_ok=True)
    date_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_name = f"cacti-rra-backup-{date_str}.tar.gz"
    archive_path = os.path.join(LOCAL_BACKUP_DIR, archive_name)

    print(f"🗜️ Compressing XML files into {archive_path} ...")
    subprocess.run(["tar", "-czf", archive_path, "-C", TMP_EXPORT_DIR, "."])
    print(f"✅ Archive created: {archive_path}")

    shutil.rmtree(TMP_EXPORT_DIR)
    return archive_path

def main():
    print("📦 Cacti RRA Backup Tool")
    stop_cron()
    try:
        export_rrds()
    finally:
        start_cron()

    archive_path = compress_export()
    print(f"\n🎉 Backup finished! File saved at: {archive_path}")

if __name__ == "__main__":
    main()
