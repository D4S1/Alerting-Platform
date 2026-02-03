resource "google_cloud_run_v2_job" "monitoring" {
  depends_on = [ google_cloud_run_service.api,
                 google_pubsub_topic.alerting,
                 google_cloud_run_service_iam_member.api_ui_monitoring_invoker
  ]
  name     = "alerting-monitoring"
  location = var.region

  template {
    template {
      service_account = google_service_account.invoker.email
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
}

resource "google_cloud_scheduler_job" "cleanup_job" {
  name             = "failure-ping-cleanup-scheduler"
  description      = "Triggers the /failures/cleanup endpoint via DELETE every 5 minutes"
  schedule         = "*/5 * * * *"
  time_zone        = "Etc/UTC"
  attempt_deadline = "320s"

  http_target {
    http_method = "DELETE"
    uri         = "${google_cloud_run_service.api.status[0].url}/failures/cleanup"
    
    oidc_token {
      service_account_email = google_service_account.invoker.email
    }
  }
}
