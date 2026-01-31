
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

        env {
          name  = "SMTP_HOST"
          value = var.smtp_host
        }

        env {
          name  = "SMTP_PORT"
          value = tostring(var.smtp_port)
        }

        env {
          name  = "SMTP_FROM"
          value = var.smtp_from
        }

        env {
          name  = "JWT_EXP_MINUTES"
          value = tostring(var.jwt_exp_minutes)
        }

        env {
          name  = "ESCALATION_DELAY_SECONDS"
          value = tostring(var.escalation_delay_seconds)
        }

        # Secrets
        env {
          name = "SMTP_USERNAME"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.smtp_username.secret_id
              version = "latest"
            }
          }
        }

        env {
          name = "SMTP_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.smtp_password.secret_id
              version = "latest"
            }
          }
        }

        env {
          name = "JWT_SECRET"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.jwt_secret.secret_id
              version = "latest"
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
