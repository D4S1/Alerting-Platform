
resource "google_cloud_run_service" "api" {
  name = "alerting-api"
  location = var.region

  template {
    spec {
      containers {
        image = var.api_image
      }
    }
  }

  traffic {
    percent = 100
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
