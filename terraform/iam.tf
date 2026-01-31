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

# Manual Access Service Account
resource "google_service_account" "manual" {
  account_id   = "manual-sa"
  display_name = "Service Account for Manual Access"
}

# IAM: API -> DB Secrets
resource "google_secret_manager_secret_iam_member" "api_db_access" {
  for_each = {
    db_username = google_secret_manager_secret.db_user.id
    db_password = google_secret_manager_secret.db_password.id
    db_host     = google_secret_manager_secret.db_host.id
    db_name     = google_secret_manager_secret.db_name.id
  }

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

# IAM: Notification -> SMTP + JWT Secrets
resource "google_secret_manager_secret_iam_member" "notification_access" {
  for_each = {
    smtp_host     = google_secret_manager_secret.smtp_host.id
    smtp_port     = google_secret_manager_secret.smtp_port.id
    smtp_from     = google_secret_manager_secret.smtp_from.id
    smtp_username = google_secret_manager_secret.smtp_username.id
    smtp_password = google_secret_manager_secret.smtp_password.id
    jwt_secret    = google_secret_manager_secret.jwt_secret.id
  }

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.notification.email}"
}


# IAM: Manual Access -> All Secrets
resource "google_secret_manager_secret_iam_member" "manual_access" {
  for_each = {
    db_username     = google_secret_manager_secret.db_user.id
    db_password     = google_secret_manager_secret.db_password.id
    db_host         = google_secret_manager_secret.db_host.id
    db_name         = google_secret_manager_secret.db_name.id
    smtp_host       = google_secret_manager_secret.smtp_host.id
    smtp_port       = google_secret_manager_secret.smtp_port.id
    smtp_from       = google_secret_manager_secret.smtp_from.id
    smtp_username   = google_secret_manager_secret.smtp_username.id
    smtp_password   = google_secret_manager_secret.smtp_password.id
    jwt_secret      = google_secret_manager_secret.jwt_secret.id
  }

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.manual.email}"
}
