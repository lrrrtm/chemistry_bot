#!/bin/bash

USER="user"
PASSWORD="password"
DATABASE="database"

BACKUP_DIR="/home"

DATE=$(date +%F)
BACKUP_FILE="$BACKUP_DIR/$DATABASE-$DATE.sql.gz"

mysqldump -u $USER -p$PASSWORD $DATABASE | gzip > $BACKUP_FILE

find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +7 -exec rm {} \;