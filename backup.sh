#!/bin/bash
# ===============================================
# Cacti Silent Backup Script for Cron
# Author: Moshiko Nayman
# ===============================================

set -euo pipefail
DATE=$(date +%F)
BACKUP_ROOT="/home/pi/cacti-backup"
ARCHIVE_DIR="$BACKUP_ROOT/cacti-archive"
LOG_FILE="$BACKUP_ROOT/backup-$DATE.log"
RRA_DIR="/var/lib/cacti/rra"
WEB_DIR="/usr/share/cacti"
MYSQL_USER="root"
MYSQL_PASSWORD="PASSWORDHERE"
DB_NAME="cacti"

mkdir -p "$ARCHIVE_DIR"

echo "[$(date)] Starting Cacti backup..." | tee -a "$LOG_FILE"

# --- 1️⃣ Backup MySQL Database ---
echo "[$(date)] Backing up MySQL database..." | tee -a "$LOG_FILE"
mysqldump --user="$MYSQL_USER" --password="$MYSQL_PASSWORD" --add-drop-table --databases "$DB_NAME" \
    > "$BACKUP_ROOT/cactidb_backup-$DATE.sql"
echo "✅ Database backup complete" | tee -a "$LOG_FILE"

# --- 2️⃣ Backup Cacti Web Files and Config ---
echo "[$(date)] Backing up Cacti web files..." | tee -a "$LOG_FILE"
cp -a "$WEB_DIR" "$BACKUP_ROOT/cacti_backup-$DATE"
echo "✅ Web files backup complete" | tee -a "$LOG_FILE"

# --- 3️⃣ Backup RRDs safely ---
echo "[$(date)] Stopping cron to safely export RRDs..." | tee -a "$LOG_FILE"
sudo systemctl stop cron

echo "[$(date)] Copying RRDs..." | tee -a "$LOG_FILE"
mkdir -p "$BACKUP_ROOT/cacti_rra-$DATE"
cp -a "$RRA_DIR"/*.rrd "$BACKUP_ROOT/cacti_rra-$DATE/"

echo "[$(date)] Converting RRDs to XML..." | tee -a "$LOG_FILE"
for rrd in "$BACKUP_ROOT/cacti_rra-$DATE"/*.rrd; do
    rrdtool dump "$rrd" > "$rrd.xml"
done

echo "[$(date)] Restarting cron..." | tee -a "$LOG_FILE"
sudo systemctl start cron
echo "✅ RRD export complete" | tee -a "$LOG_FILE"

# --- 4️⃣ Create compressed archive ---
echo "[$(date)] Creating compressed archive..." | tee -a "$LOG_FILE"
tar -czf "$ARCHIVE_DIR/cacti-backup-$DATE.tar.gz" \
    -C "$BACKUP_ROOT" \
    "cacti_backup-$DATE" "cactidb_backup-$DATE.sql" "cacti_rra-$DATE"
echo "✅ Archive created at $ARCHIVE_DIR/cacti-backup-$DATE.tar.gz" | tee -a "$LOG_FILE"

# --- 5️⃣ Cleanup old backups ---
echo "[$(date)] Cleaning up backups older than 14 days..." | tee -a "$LOG_FILE"
find "$ARCHIVE_DIR" -name "cacti-backup-*.tar.gz" -mtime +14 -exec rm {} \;
echo "✅ Cleanup complete" | tee -a "$LOG_FILE"

# --- 6️⃣ Remove temporary backup folders ---
rm -rf "$BACKUP_ROOT/cacti_backup-$DATE" \
       "$BACKUP_ROOT/cactidb_backup-$DATE.sql" \
       "$BACKUP_ROOT/cacti_rra-$DATE"

echo "[$(date)] Cacti backup finished successfully!" | tee -a "$LOG_FILE"
