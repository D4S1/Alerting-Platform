
output "api_url" {
  value = google_cloud_run_service.api.status[0].url
}

output "ui_url" {
  value = google_cloud_run_service.ui.status[0].url
}

output "pubsub_topic" {
  value = google_pubsub_topic.alerting.name
}
