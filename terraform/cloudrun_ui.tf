
resource "google_cloud_run_service" "ui" {
  name = "alerting-ui"
  location = var.region

  template {
    spec {
      containers {
        image = var.ui_image

        env {
          name  = "API_BASE_URL"
          value = google_cloud_run_service.api.status[0].url
        }
      }
    }
  }

  traffic {
    percent = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "ui_public" {
  service  = google_cloud_run_service.ui.name
  location = google_cloud_run_service.ui.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

