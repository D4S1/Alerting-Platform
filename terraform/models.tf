resource "google_cloud_run_v2_job" "db_init" {
  name       = "models-init"
  location   = var.region
  
  # Ensures IAM bindings exist before the job tries to access the secret
  depends_on = [ google_secret_manager_secret_iam_member.api_access ]

  template {
    template {
      service_account = google_service_account.api.email

      containers {
        image = var.db_image

        env {
          name = "db_url"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.db_url.secret_id
              version = "latest" 
            }
          }
        }
      }
    }
  }
}