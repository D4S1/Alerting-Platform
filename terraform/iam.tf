# API Service Account
resource "google_service_account" "api" {
  account_id   = "api-sa"
  display_name = "Service Account for API"
}

# Notification Service Account
resource "google_service_account" "notification" {
  account_id   = "notification-sa"
  display_name = "Service Account for Notifications"
}

# Invoker service account
resource "google_service_account" "invoker" {
  account_id   = "invoker-sa"
  display_name = "Invoker Cloud Run Service Account"
}


# Manual Access Service Account
resource "google_service_account" "manual" {
  account_id   = "manual-sa"
  display_name = "Service Account for Manual Access"
}

# IAM: API -> DB Secrets
resource "google_secret_manager_secret_iam_member" "api_access" {
  depends_on = [ google_secret_manager_secret.db_url,
                 google_secret_manager_secret.jwt_secret 
  ]
  
  for_each = {
    db_url     = google_secret_manager_secret.db_url.secret_id
    jwt_secret = google_secret_manager_secret.jwt_secret.secret_id
  }

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

# IAM: Notification -> SMTP + JWT Secrets
resource "google_secret_manager_secret_iam_member" "notification_access" {
  for_each = {
    smtp_host     = google_secret_manager_secret.smtp_host.secret_id
    smtp_port     = google_secret_manager_secret.smtp_port.secret_id
    smtp_from     = google_secret_manager_secret.smtp_from.secret_id
    smtp_username = google_secret_manager_secret.smtp_username.secret_id
    smtp_password = google_secret_manager_secret.smtp_password.secret_id
    jwt_secret    = google_secret_manager_secret.jwt_secret.secret_id
  }

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.notification.email}"
}


# IAM: Manual Access -> All Secrets
resource "google_secret_manager_secret_iam_member" "manual_access" {
  for_each = {
    db_url          = google_secret_manager_secret.db_url.secret_id
    smtp_host       = google_secret_manager_secret.smtp_host.secret_id
    smtp_port       = google_secret_manager_secret.smtp_port.secret_id
    smtp_from       = google_secret_manager_secret.smtp_from.secret_id
    smtp_username   = google_secret_manager_secret.smtp_username.secret_id
    smtp_password   = google_secret_manager_secret.smtp_password.secret_id
    jwt_secret      = google_secret_manager_secret.jwt_secret.secret_id
  }

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.manual.email}"
}


resource "google_cloud_run_service_iam_member" "api_ui_monitoring_invoker" {
  service  = google_cloud_run_service.api.name
  location = google_cloud_run_service.api.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.invoker.email}"
}

resource "google_cloud_run_service_iam_member" "api_notification_invoker" {
  service  = google_cloud_run_service.api.name
  location = google_cloud_run_service.api.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.notification.email}"
}


resource "google_cloud_run_service_iam_member" "api_manual_invoker" {
  service  = google_cloud_run_service.api.name
  location = google_cloud_run_service.api.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.manual.email}"
}

# Cloud Tasks configuration
resource "google_service_account_iam_member" "notification_tasks_impersonation" {
  service_account_id = google_service_account.notification.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.notification.email}"
}

resource "google_cloud_run_service_iam_member" "notification_invoker_itself" {
  service  = google_cloud_run_service.notification.name
  location = google_cloud_run_service.notification.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.notification.email}"
}

resource "google_project_iam_member" "notification_task_creator" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.notification.email}"
}

# IAM: Invoker -> PubSub Publisher
resource "google_pubsub_topic_iam_member" "invoker_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.alerting.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.invoker.email}"
}

resource "google_pubsub_subscription" "alerting_push" {
  name  = "alerting-notification-push"
  topic = google_pubsub_topic.alerting.name
  
  ack_deadline_seconds = 20

  push_config {
    # "/event" is a notification engine endpoint
    push_endpoint = "${google_cloud_run_service.notification.status[0].url}/event"

    # Invoker account for authorization
    oidc_token {
      service_account_email = google_service_account.invoker.email
    }
  }
}

resource "google_cloud_run_service_iam_member" "notification_push_invoker" {
  service  = google_cloud_run_service.notification.name
  location = google_cloud_run_service.notification.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.invoker.email}"
}