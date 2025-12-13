# Alerting-Platform
Alerting platform that monitors HTTP services, sends email notifications to administrators, escalates alerts automatically, and maintains full audit logging. The platform is simple to deploy on Google Cloud, testable locally.

### Dummy database setup

```
python utils/dummy_db.py \     
  -s 3 \
  -i 5 \
  -db database/monitoring.db
```

FOr viewing recommend `SQLite Viewer` extention in Visual Studio Code