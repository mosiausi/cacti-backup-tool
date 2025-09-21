# Cacti Backup Tool

Created by: Moshiko Nayman

This is a Python-based CLI tool for backing up and restoring your Cacti monitoring system. It guides you through the process, validates the backup contents, and optionally compresses everything into a single `.tar.gz` file for easy portability.

## Features

- 🔄 Full backup of Cacti web files, config, data, and database
- 🧠 Validation report to confirm backup integrity
- 🗜️ Optional compression into a dated archive
- 🔁 Restore functionality for plug-and-play recovery
- 🧾 Clear CLI prompts and confirmations

## Requirements

- Python 3.6+
- `mysqldump` and `mysql` CLI tools
- Sudo/root access for file operations

## Usage

```bash
sudo python3 cacti_tool.py
