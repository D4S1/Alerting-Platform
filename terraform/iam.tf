resource "google_project_iam_member" "cloudrun_secrets" {
  role   = "roles/secretmanager.secretAccessor"
  member = "serviceAccount:${google_service_account.app.email}"
}