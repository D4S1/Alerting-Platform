resource "google_cloud_run_service" "api" {
  name     = "alerting-api"
  location = var.region

  template {
    spec {
      containers {
        image = var.api_image

        env {
          name = "db_user"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.db_user.id
              key    = "db_user"
            }
          }
        }

        env {
          name = "db_password"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.db_password.id
              key    = "db_password"
            }
          }
        }

        env {
          name = "db_name"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.db_name.id
              key    = "db_name"
            }
          }
        }

        env {
          name = "db_host"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.db_host.id
              key    = "db_host"
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
