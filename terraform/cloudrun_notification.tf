
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
      }
    }
  }

  traffic {
    percent = 100
    latest_revision = true
  }
}
