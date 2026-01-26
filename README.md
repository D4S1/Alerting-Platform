# Alerting-Platform
Alerting platform that monitors HTTP services, sends email notifications to administrators, escalates alerts automatically, and maintains full audit logging. The platform is simple to deploy on Google Cloud, testable locally.

## Dummy database setup

```
python utils/dummy_db.py \     
  -s 3 \
  -i 5 \
  -db database/monitoring.db
```

FOr viewing recommend `SQLite Viewer` extention in Visual Studio Code


## How to run API

```
uvicorn api.main:app --reload
```

### Service enpoints

Creates new service
```
curl -X POST "http://localhost:8000/services" \
-H "Content-Type: application/json" \
-d '{
  "name": "<name>",
  "IP": "<url>",
  "frequency_seconds": 5,
  "alerting_window_npings": 10
}'
```

Deletes the service
```
curl -X DELETE "http://localhost:8000/services/1"
```

### Incident endpoints

Creates new incident for service id=1
```
curl -X POST "http://localhost:8000/services/<service_id>/incidents"
```
List all incidents for given service
```
curl -X GET "http://localhost:8000/services/<service_id>/incidents"
```
List open incidents for given service
```
curl -X GET "http://localhost:8000/services/<service_id>/incidents/open" 
```
Changes the status
```
curl -X PATCH "http://localhost:8000/incidents/<incident_id>/status?status=<status>" 
```
Closes the incident (sets ended_at to current time)
```
curl -X PATCH "http://localhost:8000/incidents/<incident_id>/resolve" 
```

## Notification engine
### Environment configuration

1. Copy example file:
```bash
cp .env.example .env
```
2. Fill in the values ​​in .env:

| Variable                 | Description                                | Example / Default            |
|--------------------------|--------------------------------------------|------------------------------|
| SMTP_HOST                | Address of the SMTP server                 | smtp.gmail.com               |
| SMTP_PORT                | Port for the SMTP server                   | 587 (default)                |
| SMTP_USERNAME            | Username (usually email address)           | user@example.com             |
| SMTP_PASSWORD            | Password or App Password                   | your-secret-password         |
| SMTP_FROM                | Email address shown as the sender          | notifications@yourdomain.com |
| JWT_SECRET               | Secret key for signing ACK tokens          | long-random-string-here      |
| JWT_EXP_MINUTES          | Token expiration time in minutes           | 15 (default)                 |
| ESCALATION_DELAY_SECONDS | Delay before escalating to secondary admin | 300 (5 minutes)              |