resource "null_resource" "init_db" {
  # Make this run after secrets are created
  depends_on = [
    google_secret_manager_secret_version.db_user_v,
    google_secret_manager_secret_version.db_password_v,
    google_secret_manager_secret_version.db_name_v,
    google_secret_manager_secret_version.db_host_v
  ]

  provisioner "local-exec" {
    working_dir = "../"
    command = <<EOT
      export DB_USER=$(gcloud secrets versions access latest --secret=DB_USER)
      export DB_PASSWORD=$(gcloud secrets versions access latest --secret=DB_PASSWORD)
      export DB_NAME=$(gcloud secrets versions access latest --secret=DB_NAME)
      export DB_HOST=$(gcloud secrets versions access latest --secret=DB_HOST)
      python utils/db_init_cloudsql.py
    EOT
  }
}
