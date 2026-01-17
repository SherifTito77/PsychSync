# Backup service Dockerfile
FROM alpine:3.18

# Install required packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    postgresql-client \
    curl \
    aws-cli \
    bash \
    cron

# Set working directory
WORKDIR /app

# Copy backup script
COPY deployment/backup.sh /usr/local/bin/backup.sh
RUN chmod +x /usr/local/bin/backup.sh

# Copy Python backup utilities
COPY deployment/backup_utils.py /app/backup_utils.py

# Install Python dependencies
RUN pip3 install psycopg2-binary boto3 python-dotenv

# Create backup directory
RUN mkdir -p /backups && \
    addgroup -g 1000 backup && \
    adduser -D -s /bin/sh -u 1000 -G backup backup

# Set ownership
RUN chown -R backup:backup /app /backups

# Switch to backup user
USER backup

# Setup cron job
RUN echo "0 2 * * * /usr/local/bin/backup.sh" > /tmp/crontab && \
    crontab /tmp/crontab

# Start cron daemon
CMD ["crond", "-f", "-l", "8"]
