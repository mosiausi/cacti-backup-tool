#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Cacti Backup & Restore Tool (Number Menu + Compression + Fixed Restore)
# Author: Moshiko Nayman (modified)

import os
import shutil
import subprocess
import datetime

# ====== CONFIG ======
BACKUP_ROOT = os.path.join(os.getcwd(), "cacti_manual_backups")
MYSQL_USER = "root"
MYSQL_PASSWORD = "PASSWORDHERE"
DB_NAME = "cacti"
# ====================


def menu(prompt, options):
    """Number-based selection menu"""
    print(f"\n{prompt}")
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    while True:
        choice = input("Select option number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return int(choice)
        else:
            print("❌ Invalid choice, try again.")


def make_timestamp_dir(suffix=""):
    """Create timestamped folder under BACKUP_ROOT"""
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{date_str}{suffix}"
    backup_dir = os.path.join(BACKUP_ROOT, folder_name)
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def compress_backup_folder(folder_path):
    """Compress a folder into .tar.gz and remove the original folder"""
    archive_path = f"{folder_path}.tar.gz"
    print(f"🗜️ Compressing backup to {archive_path} ...")
    subprocess.run(
        ["tar", "-czf", archive_path, "-C", os.path.dirname(folder_path), os.path.basename(folder_path)]
    )
    shutil.rmtree(folder_path)
    print(f"✅ Backup compressed: {archive_path}")
    return archive_path


def convert_rrd_to_xml(src_dir, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    for root, _, files in os.walk(src_dir):
        rel_root = os.path.relpath(root, src_dir)
        out_dir = os.path.join(dest_dir, rel_root)
        os.makedirs(out_dir, exist_ok=True)
        for f in files:
            if f.endswith(".rrd"):
                rrd_path = os.path.join(root, f)
                xml_path = os.path.join(out_dir, f + ".xml")
                subprocess.run(["rrdtool", "dump", rrd_path, xml_path], check=False)


# === FULL BACKUP ===
def backup_full():
    backup_dir = make_timestamp_dir("_full")
    print("\n🔄 Starting FULL backup...")
    print("⏹️ Stopping cron jobs...")
    subprocess.run(["systemctl", "stop", "cron"], check=False)

    paths = {
        "/usr/share/cacti": "cacti_files",
        "/etc/cacti": "cacti_config",
        "/var/lib/cacti": "cacti_data",
    }

    for src, name in paths.items():
        dest = os.path.join(backup_dir, name)
        if name == "cacti_data":
            print("📝 Converting RRD files to XML...")
            convert_rrd_to_xml(src, dest)
        else:
            shutil.copytree(src, dest, dirs_exist_ok=True)
        print(f"✅ Backed up {src} → {dest}")

    print("🧠 Dumping MySQL database...")
    dump_file = os.path.join(backup_dir, "cacti.sql")
    with open(dump_file, "w") as f:
        subprocess.run(["mysqldump", "-u", MYSQL_USER, f"-p{MYSQL_PASSWORD}", DB_NAME], stdout=f)
    print(f"✅ Database dumped to {dump_file}")

    print("▶️ Restarting cron jobs...")
    subprocess.run(["systemctl", "start", "cron"], check=False)

    # Compress backup
    archive_file = compress_backup_folder(backup_dir)
    print(f"🎉 FULL backup complete! Compressed archive at: {archive_file}")


# === RRD BACKUP ONLY ===
def backup_rrd_only():
    backup_dir = make_timestamp_dir("_rrd")
    print("\n🔄 Starting RRD-only backup...")
    print("⏹️ Stopping cron jobs...")
    subprocess.run(["systemctl", "stop", "cron"], check=False)

    src = "/var/lib/cacti/rra"
    dest = os.path.join(backup_dir, "cacti_rra")
    print("📝 Converting RRD files to XML...")
    convert_rrd_to_xml(src, dest)
    print(f"✅ RRD backup saved to {dest}")

    print("▶️ Restarting cron jobs...")
    subprocess.run(["systemctl", "start", "cron"], check=False)

    # Compress backup
    archive_file = compress_backup_folder(backup_dir)
    print(f"\n🎉 RRD-only backup complete! Compressed archive at: {archive_file}")


# === RESTORE ===
def restore():
    print("\nAvailable backups in:", BACKUP_ROOT)
    backups = sorted([d for d in os.listdir(BACKUP_ROOT)])
    if not backups:
        print("❌ No backups found.")
        return

    choice = menu("Select a backup folder/archive to restore:", backups + ["Cancel"])
    if choice == len(backups) + 1:
        print("❌ Restore cancelled.")
        return

    backup_item = backups[choice - 1]
    backup_path = os.path.join(BACKUP_ROOT, backup_item)

    working_dir = None
    temp_extract_dir = None

    # If it’s a tar.gz archive, extract it
    if backup_item.endswith(".tar.gz"):
        temp_extract_dir = os.path.join(
            BACKUP_ROOT, f"tmp_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        os.makedirs(temp_extract_dir, exist_ok=True)
        print(f"📦 Extracting {backup_item} ...")
        subprocess.run(["tar", "-xzf", backup_path, "-C", temp_extract_dir], check=False)

        # If archive contains a single folder, dive into it
        extracted_items = os.listdir(temp_extract_dir)
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_extract_dir, extracted_items[0])):
            working_dir = os.path.join(temp_extract_dir, extracted_items[0])
        else:
            working_dir = temp_extract_dir
    else:
        # Backup is already a folder
        working_dir = backup_path

    print(f"\n🔁 Starting restore from {backup_item} ...")
    print("⏹️ Stopping cron jobs...")
    subprocess.run(["systemctl", "stop", "cron"], check=False)

    paths = {
        "cacti_files": "/usr/share/cacti",
        "cacti_config": "/etc/cacti",
        "cacti_data": "/var/lib/cacti",
    }

    for name, dest in paths.items():
        src = os.path.join(working_dir, name)
        if os.path.exists(src):
            shutil.copytree(src, dest, dirs_exist_ok=True)
            print(f"✅ Restored {src} → {dest}")

    sql_file = os.path.join(working_dir, "cacti.sql")
    if os.path.exists(sql_file):
        print("🧠 Restoring MySQL database...")
        with open(sql_file, "r") as f:
            subprocess.run(["mysql", "-u", MYSQL_USER, f"-p{MYSQL_PASSWORD}", DB_NAME], stdin=f)
        print("✅ Database restored")

    print("▶️ Restarting cron jobs...")
    subprocess.run(["systemctl", "start", "cron"], check=False)

    if temp_extract_dir:
        try:
            shutil.rmtree(temp_extract_dir)
            print(f"🧹 Cleaned up temporary folder {temp_extract_dir}")
        except Exception as e:
            print(f"⚠️ Could not remove temp folder: {e}")

    print("🎉 Restore complete!")


# === MAIN ===
def main():
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    print("📦 Welcome to the Cacti Backup & Restore Tool")

    while True:
        choice = menu("Select operation:", ["Full Cacti Backup", "RRD Backup Only", "Restore", "Exit"])
        if choice == 1:
            backup_full()
        elif choice == 2:
            backup_rrd_only()
        elif choice == 3:
            restore()
        else:
            print("👋 Exiting tool.")
            break


if __name__ == "__main__":
    main()
