# Alerting-Platform

**Alerting-Platform** is a cloud-native solution that monitors HTTP services, triggers automated alerts, escalates incidents, and maintains full audit logging. The platform is designed to be **lightweight, highly configurable, and easy to deploy on Google Cloud**, with a focus on operational simplicity, reliability, and developer-friendliness for CI/CD automation.

---

## Features

- **Continuous Monitoring:** Periodically checks HTTP endpoints at administrator-defined intervals.  
- **Automated Incident Management:** Detects incidents based on configurable failure thresholds.  
- **Notification & Escalation:** Sends email notifications to primary and secondary administrators.  
- **Acknowledgment Workflow:** Administrators can acknowledge incidents via email or UI.  
- **Audit Logging:** Tracks all notification attempts, acknowledgments, and incident resolutions.  
- **Cloud-Native Architecture:** Serverless deployment using Cloud Run, Pub/Sub, and Cloud SQL.  
- **Lightweight UI:** Web interface for registering services, managing administrators, and acknowledging incidents.  
- **Developer-Friendly:** Dockerized services and Terraform-based infrastructure for repeatable deployments.  

---

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="graphics/dataflow-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="graphics/dataflow-light.png">
  <img alt="Shows a black logo in light color mode and a white one in dark color mode." src="https://user-images.githubusercontent.com/25423296/163456779-a8556205-d0a5-45e2-ac17-42d089e3c3f8.png">
</picture>


<picture>
  <source media="(prefers-color-scheme: dark)" srcset="graphics/architecture-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="graphics/architecture-light.png">
  <img alt="Shows a black logo in light color mode and a white one in dark color mode." src="https://user-images.githubusercontent.com/25423296/163456779-a8556205-d0a5-45e2-ac17-42d089e3c3f8.png">
</picture>


---

## Deployment

### Prerequisites

Before deploying, ensure the following tools and services are available:

- Google Cloud account with **project creation permissions**  
- [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs)  
- [Docker](https://www.docker.com/get-started)  
- [Terraform](https://www.terraform.io/downloads)  
- SMTP credentials for email notifications  

---

### Artifact Registry

Artifact Registry is used to store Docker images for the platform. Follow these steps to configure it:

1. **Create the Artifact Registry:**

```bash
gcloud artifacts repositories create <registry-repo> \
    --repository-format=docker \
    --location=<region> \
    --description="Artifact registry for Alerting-Platform"
```

2. **Configure Docker authentication for your region:**

```bash
gcloud auth configure-docker <region>-docker.pkg.dev
```

---

### Docker

All components are containerized. Dockerfiles are located in the `docker` folder:

- `api.Dockerfile` – API microservice  
- `monitoring.Dockerfile` – Monitoring Engine  
- `notification.Dockerfile` – Notification Engine  
- `ui.Dockerfile` – Administrator UI  
- `db.Dockerfile` – Database initialization and utilities  

**Build and push Docker images to Artifact Registry:**

```bash
docker buildx build -f docker/<component>.Dockerfile \
    -t <region>-docker.pkg.dev/<project-name>/<registry-repo>/<component>:<tag> .
docker push <region>-docker.pkg.dev/<project-name>/<registry-repo>/<component>:<tag>
```

Replace:

- `<component>` – api, monitoring, notification, ui, or db  
- `<region>` – Artifact Registry region  
- `<project-name>` – GCP project ID  
- `<registry-repo>` – Artifact Registry repository  
- `<tag>` – image version tag (e.g., `v1.0.0`)  

> **Pro Tip:** Use consistent semantic versioning across all images to simplify deployment and rollback.

---

### Infrastructure

Infrastructure is provisioned using **Terraform**, ensuring repeatable, environment-agnostic deployments.

**Required variables:**

- `project_name` – Google Cloud project ID  
- `region` – Deployment region  
- `docker_views_location` – Path to Docker images in Artifact Registry  
- `smtp_domain` – SMTP domain for email notifications  
- `smtp_password` – SMTP password (stored securely in Secret Manager)  

**Deploy infrastructure:**

```bash
cd terraform
terraform init
terraform apply
```

**Terraform provisions:**

- Cloud Run services for API, UI, and Notification Engine  
- Cloud Run Job for Monitoring Engine
- Cloud SQL PostgreSQL database  
- Pub/Sub topics for incident notifications  
- Secret Manager entries for SMTP, DB credentials and API secrets  
- Cloud IAM roles for service accounts and secure access  

> **Security Note:** Terraform ensures sensitive information (e.g., SMTP passwords) is stored securely and not hard-coded.

