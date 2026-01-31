resource "google_cloud_run_service" "notification" {
  depends_on = [google_secret_manager_secret_iam_member.notification_access,
                google_pubsub_topic.alerting,
                google_cloud_run_service_iam_member.api_notification_invoker
  ]
  
  name     = "alerting-notification"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.notification.email

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
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.smtp_host.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "SMTP_PORT"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.smtp_port.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "SMTP_FROM"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.smtp_from.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "SMTP_USERNAME"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.smtp_username.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "SMTP_PASSWORD"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.smtp_password.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "JWT_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.jwt_secret.secret_id
              key  = "latest"
            }
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}
