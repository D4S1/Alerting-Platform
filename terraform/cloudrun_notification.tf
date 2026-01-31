
resource "google_cloud_run_service" "notification" {
  name = "alerting-notification"
  location = var.region

  template {
    spec {
      containers {
        image = var.notification_image

        env {
          name  = "API_BASE_URL"
          value = google_cloud_run_service.api.status[0].url
        }

        env {
          name  = "PUBSUB_TOPIC"
          value = google_pubsub_topic.alerting.id
        }

        # SMTP secrets
        env {
          name = "SMTP_HOST"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.smtp_host.secret_id
              version = "latest"
            }
          }
        }

        env {
          name = "SMTP_PORT"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.smtp_port.secret_id
              version = "latest"
            }
          }
        }

        env {
          name = "SMTP_FROM"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.smtp_from.secret_id
              version = "latest"
            }
          }
        }

        env {
          name = "SMTP_USERNAME"
          value_from {
            secret_key_ref {
              name  = google_secret_manager_secret.smtp_username.secret_id
              key = "SMTP_USERNAME"
            }
          }
        }

        env {
          name = "SMTP_PASSWORD"
          value_from {
            secret_key_ref {
              name  = google_secret_manager_secret.smtp_password.secret_id
              key = "SMTP_PASSWORD"
            }
          }
        }

        env {
          name = "JWT_SECRET"
          value_from {
            secret_key_ref {
              name  = google_secret_manager_secret.jwt_secret.secret_id
              key = "JWT_SECRET"
            }
          }
        }
      }
    }
  }

  traffic {
    percent = 100
    latest_revision = true
  }
}
