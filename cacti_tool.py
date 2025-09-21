#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Cacti Backup & Restore Tool
# Created by: Moshiko Nayman
# Description: Interactive CLI tool to backup and restore Cacti with validation and optional compression.

import os
import shutil
import subprocess
import datetime

BACKUP_ROOT = "/opt"
BACKUP_FOLDER = "cacti_backup"
BACKUP_DIR = os.path.join(BACKUP_ROOT, BACKUP_FOLDER)
MYSQL_USER = "root"
MYSQL_PASSWORD = "your_password"
DB_NAME = "cacti"

def explain_backup():
    print("\n🧾 Backup Overview:")
    print("- This will create a full backup of your Cacti installation.")
    print("- It includes:")
    print("  • Web files from /usr/share/cacti")
    print("  • Configuration files from /etc/cacti")
    print("  • Data files from /var/lib/cacti")
    print("  • A MySQL database dump of the 'cacti' database")
    print(f"- Backup will be stored in: {BACKUP_DIR}\n")

def explain_restore():
    print("\n🧾 Restore Overview:")
    print("- This will restore your Cacti installation from a previous backup.")
    print("- It will:")
    print("  • Overwrite existing Cacti files and configs")
    print("  • Restore the MySQL database from the backup")
    print(f"- Source backup folder: {BACKUP_DIR}\n")

def confirm():
    choice = input("❓ Do you want to proceed? Type 'yes' to continue: ").strip().lower()
    return choice == "yes"

def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    print("\n🔄 Starting backup...")

    paths = {
        "/usr/share/cacti": "cacti_files",
        "/etc/cacti": "cacti_config",
        "/var/lib/cacti": "cacti_data"
    }

    for src, name in paths.items():
        dest = os.path.join(BACKUP_DIR, name)
        shutil.copytree(src, dest, dirs_exist_ok=True)
        print(f"✅ Backed up {src} → {dest}")

    print("🧠 Dumping MySQL database...")
    dump_file = os.path.join(BACKUP_DIR, "cacti.sql")
    subprocess.run([
        "mysqldump", "-u", MYSQL_USER, f"-p{MYSQL_PASSWORD}", DB_NAME
    ], stdout=open(dump_file, "w"))
    print(f"✅ Database dumped to {dump_file}")

    verify_backup()
    offer_compression()

def restore():
    print("\n🔁 Starting restore...")

    paths = {
        "cacti_files": "/usr/share/cacti",
        "cacti_config": "/etc/cacti",
        "cacti_data": "/var/lib/cacti"
    }

    for name, dest in paths.items():
        src = os.path.join(BACKUP_DIR, name)
        shutil.copytree(src, dest, dirs_exist_ok=True)
        print(f"✅ Restored {src} → {dest}")

    print("🧠 Restoring MySQL database...")
    dump_file = os.path.join(BACKUP_DIR, "cacti.sql")
    subprocess.run([
        "mysql", "-u", MYSQL_USER, f"-p{MYSQL_PASSWORD}", DB_NAME
    ], stdin=open(dump_file, "r"))
    print("✅ Database restored")

def verify_backup():
    print("\n🔍 Backup Validation Report:")

    checks = {
        "Web files": "cacti_files",
        "Config files": "cacti_config",
        "Data files": "cacti_data"
    }

    for label, folder in checks.items():
        full_path = os.path.join(BACKUP_DIR, folder)
        file_count = sum(len(files) for _, _, files in os.walk(full_path)) if os.path.exists(full_path) else 0
        if file_count > 0:
            print(f"✅ {label}: {file_count} files found in {full_path}")
        else:
            print(f"⚠️ {label}: No files found or folder missing ({full_path})")

    sql_path = os.path.join(BACKUP_DIR, "cacti.sql")
    if os.path.exists(sql_path):
        size_kb = os.path.getsize(sql_path) // 1024
        if size_kb > 1:
            print(f"✅ SQL Dump: {size_kb} KB at {sql_path}")
        else:
            print(f"⚠️ SQL Dump: File too small ({size_kb} KB) — may be incomplete")
    else:
        print(f"❌ SQL Dump: File not found at {sql_path}")

    print("\n📋 Validation complete. Review any warnings before relying on this backup.")

def offer_compression():
    choice = input("\n📦 Do you want to compress the backup into a single .tar.gz file? Type 'yes' to proceed: ").strip().lower()
    if choice != "yes":
        print("🛑 Compression skipped.")
        return

    date_str = datetime.datetime.now().strftime("%Y%m%d")
    archive_name = f"cacti-backup-{date_str}.tar.gz"
    archive_path = os.path.join(BACKUP_ROOT, archive_name)

    print(f"\n🗜️ Compressing backup to {archive_path}...")
    subprocess.run(["tar", "-czf", archive_path, "-C", BACKUP_ROOT, BACKUP_FOLDER])
    shutil.rmtree(BACKUP_DIR)
    print(f"✅ Compression complete. Original folder removed. Final backup: {archive_path}")

def main():
    print("📦 Welcome to the Cacti Backup & Restore Tool")
    choice = input("👉 Type 'backup' or 'restore' to begin: ").strip().lower()

    if choice == "backup":
        explain_backup()
        if confirm():
            backup()
        else:
            print("❌ Backup cancelled.")
    elif choice == "restore":
        explain_restore()
        if confirm():
            restore()
        else:
            print("❌ Restore cancelled.")
    else:
        print("❌ Invalid choice. Please type 'backup' or 'restore'.")

if __name__ == "__main__":
    main()
