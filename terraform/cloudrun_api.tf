resource "google_cloud_run_service" "api" {
  name     = "alerting-api"
  location = var.region

  template {
    spec {
      containers {
        image = var.api_image

        env {
          name = "DB_USER"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.db_user.id
              key    = "DB_USER"
            }
          }
        }

        env {
          name = "DB_PASSWORD"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.db_password.id
              key    = "DB_PASSWORD"
            }
          }
        }

        env {
          name = "DB_NAME"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.db_name.id
              key    = "DB_NAME"
            }
          }
        }

        env {
          name = "DB_HOST"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.db_host.id
              key    = "DB_HOST"
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

resource "google_secret_manager_secret" "api_url" {
  secret_id = "API_BASE_URL"
  replication {
  auto {}
}
}

resource "google_secret_manager_secret_version" "api_url_v" {
  depends_on = [google_cloud_run_service.api]
  secret = google_secret_manager_secret.api_url.id
  secret_data = google_cloud_run_service.api.status[0].url
}
