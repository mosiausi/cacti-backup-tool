#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Cacti Backup & Restore Tool
# Created by: Moshiko Nayman
# Extended with safe RRD backup/restore logic

import os
import shutil
import subprocess
import datetime

BACKUP_ROOT = "/opt"
BACKUP_FOLDER = "cacti_backup"
BACKUP_DIR = os.path.join(BACKUP_ROOT, BACKUP_FOLDER)
MYSQL_USER = "root"
MYSQL_PASSWORD = "PASSWORDHERE"
DB_NAME = "cacti"
RRA_DIR = "/var/lib/cacti/rra"   # adjust if your RRAs live elsewhere

def stop_cron():
    print("🛑 Stopping poller cron jobs...")
    subprocess.run(["systemctl", "stop", "cron"], check=False)

def start_cron():
    print("▶️ Restarting poller cron jobs...")
    subprocess.run(["systemctl", "start", "cron"], check=False)

def export_rrds(dest_dir):
    print("📤 Exporting RRDs to XML...")
    xml_dir = os.path.join(dest_dir, "rrd_xml")
    os.makedirs(xml_dir, exist_ok=True)

    for root, _, files in os.walk(RRA_DIR):
        for f in files:
            if f.endswith(".rrd"):
                rrd_path = os.path.join(root, f)
                xml_path = os.path.join(xml_dir, f + ".xml")
                subprocess.run(["rrdtool", "dump", rrd_path, xml_path])
    print(f"✅ Exported RRDs to {xml_dir}")

def restore_rrds(src_dir):
    print("📥 Restoring RRDs from XML...")
    xml_dir = os.path.join(src_dir, "rrd_xml")
    os.makedirs(RRA_DIR, exist_ok=True)

    for root, _, files in os.walk(xml_dir):
        for f in files:
            if f.endswith(".xml"):
                xml_path = os.path.join(root, f)
                rrd_path = os.path.join(RRA_DIR, f.replace(".xml", ""))
                subprocess.run(["rrdtool", "restore", xml_path, rrd_path])
    print(f"✅ Restored RRDs to {RRA_DIR}")

def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    print("\n🔄 Starting backup...")

    stop_cron()

    paths = {
        "/usr/share/cacti": "cacti_files",
        "/etc/cacti": "cacti_config"
    }

    for src, name in paths.items():
        dest = os.path.join(BACKUP_DIR, name)
        shutil.copytree(src, dest, dirs_exist_ok=True)
        print(f"✅ Backed up {src} → {dest}")

    export_rrds(BACKUP_DIR)

    print("🧠 Dumping MySQL database...")
    dump_file = os.path.join(BACKUP_DIR, "cacti.sql")
    subprocess.run([
        "mysqldump", "-u", MYSQL_USER, f"-p{MYSQL_PASSWORD}", DB_NAME
    ], stdout=open(dump_file, "w"))
    print(f"✅ Database dumped to {dump_file}")

    start_cron()
    verify_backup()
    offer_compression()

def restore():
    print("\n🔁 Starting restore...")

    stop_cron()

    paths = {
        "cacti_files": "/usr/share/cacti",
        "cacti_config": "/etc/cacti"
    }

    for name, dest in paths.items():
        src = os.path.join(BACKUP_DIR, name)
        shutil.copytree(src, dest, dirs_exist_ok=True)
        print(f"✅ Restored {src} → {dest}")

    restore_rrds(BACKUP_DIR)

    print("🧠 Restoring MySQL database...")
    dump_file = os.path.join(BACKUP_DIR, "cacti.sql")
    subprocess.run([
        "mysql", "-u", MYSQL_USER, f"-p{MYSQL_PASSWORD}", DB_NAME
    ], stdin=open(dump_file, "r"))
    print("✅ Database restored")

    start_cron()

# keep the rest (verify_backup, offer_compression, main) as in your script
