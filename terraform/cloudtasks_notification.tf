resource "google_project_service" "cloud_tasks_api" {
  project = var.project_id
  service = "cloudtasks.googleapis.com"
  disable_on_destroy = false
}

resource "google_cloud_tasks_queue" "notifications" {
  name     = "notifications-queue"
  location = var.region

  retry_config {
    max_attempts = 5
  }

  depends_on = [
    google_project_service.cloud_tasks_api
  ]
}
