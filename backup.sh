#!/bin/bash
# ===============================================
# Cacti Silent Backup Script for Cron
# Author: Moshiko Nayman
# ===============================================
set -euo pipefail

# ===== CONFIG =====
BACKUP_ROOT="/home/pi/cacti-backup"
BACKUP_ARCHIVE_DIR="$BACKUP_ROOT/cacti-archive"
RRA_DIR="/var/lib/cacti/rra"
MYSQL_USER="root"
MYSQL_PASSWORD="PASSWORDHERE"
DB_NAME="cacti"
LOG_FILE="$BACKUP_ROOT/backup-$(date +%F).log"
KEEP_LOG_DAYS=14
KEEP_BACKUP_DAYS=14

mkdir -p "$BACKUP_ARCHIVE_DIR"

# ===== Logging =====
exec > >(tee -a "$LOG_FILE") 2>&1
echo "===== Backup started at $(date) ====="

# ===== Stop cron for safe RRD export =====
echo "Stopping cron for RRD export..."
sudo systemctl stop cron || true

# ===== Backup MySQL Database =====
echo "Backing up MySQL database..."
mysqldump --user="$MYSQL_USER" --password="$MYSQL_PASSWORD" --add-drop-table "$DB_NAME" > "$BACKUP_ROOT/cactidb_backup-$(date +%F).sql"

# ===== Backup Cacti files & configs =====
echo "Backing up Cacti web and config directories..."
cp -a /usr/share/cacti "$BACKUP_ROOT/cacti_backup-$(date +%F)"
cp -a /etc/cacti "$BACKUP_ROOT/cacti_config-$(date +%F)"

# ===== Backup and Export RRDs =====
echo "Backing up RRD files..."
mkdir -p "$BACKUP_ROOT/cacti_rra"
cp -a "$RRA_DIR/"*.rrd "$BACKUP_ROOT/cacti_rra"

echo "Converting RRDs to XML..."
for i in "$BACKUP_ROOT"/cacti_rra/*.rrd; do
    rrdtool dump "$i" > "$i.xml"
done

# ===== Restart cron =====
echo "Restarting cron..."
sudo systemctl start cron || true

# ===== Create compressed archive =====
ARCHIVE_NAME="cacti-prod-$(date +%F).tar.gz"
echo "Creating archive $ARCHIVE_NAME..."
tar -czf "$BACKUP_ARCHIVE_DIR/$ARCHIVE_NAME" -C "$BACKUP_ROOT" cacti_backup* cacti_config* cactidb_backup* cacti_rra*

# ===== Cleanup temporary backup folders =====
echo "Cleaning temporary backup folders..."
rm -rf "$BACKUP_ROOT"/cacti_backup* "$BACKUP_ROOT"/cacti_config* "$BACKUP_ROOT"/cactidb_backup* "$BACKUP_ROOT"/cacti_rra*

# ===== Cleanup old logs =====
echo "Removing logs older than $KEEP_LOG_DAYS days..."
find "$BACKUP_ROOT" -name "backup-*.log" -mtime +"$KEEP_LOG_DAYS" -exec rm {} \;

# ===== Cleanup old backups =====
echo "Removing backups older than $KEEP_BACKUP_DAYS days..."
find "$BACKUP_ARCHIVE_DIR" -name "cacti-prod-*.tar.gz" -mtime +"$KEEP_BACKUP_DAYS" -exec rm {} \;

echo "===== Backup completed at $(date) ====="
