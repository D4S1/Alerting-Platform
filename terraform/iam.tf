resource "google_project_iam_member" "cloudrun_secrets" {
  role   = "roles/secretmanager.secretAccessor"
  member = "serviceAccount:${google_service_account.app.email}"
}

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
  member    = "serviceAccount:${google_cloud_run_service.notification.template[0].spec[0].service_account_name}"
}
