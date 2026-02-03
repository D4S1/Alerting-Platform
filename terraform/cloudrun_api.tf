resource "google_cloud_run_service" "api" {
  depends_on = [google_secret_manager_secret_iam_member.api_access]
  name     = "alerting-api"
  location = var.region

  template {
    metadata {
      annotations = {
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.postgres.connection_name
      }
    }
    spec {
      service_account_name = google_service_account.api.email

      containers {
        image = var.api_image

        env {
          name = "db_url"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.db_url.secret_id
              key = "latest"
            }
          }
        }

        env {
          name = "jwt_secret"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.jwt_secret.secret_id
              key = "latest"
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

resource "google_project_iam_member" "api_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_secret_manager_secret_iam_member" "api_db_access" {
  secret_id = google_secret_manager_secret.db_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}