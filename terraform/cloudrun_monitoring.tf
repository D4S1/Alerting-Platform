
resource "google_cloud_run_service" "monitoring" {
  name = "alerting-monitoring"
  location = var.region

  template {
    spec {
      containers {
        image = var.monitoring_image

        env {
          name  = "API_BASE_URL"
          value = google_cloud_run_service.api.status[0].url
        }

        env {
          name  = "PUBSUB_TOPIC"
          value = google_pubsub_topic.alerting.id
        }
      }
    }
  }

  traffic {
    percent = 100
    latest_revision = true
  }
}
