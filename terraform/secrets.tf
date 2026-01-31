
resource "google_secret_manager_secret" "db_host" {
  secret_id = "db_host"
  replication {
  auto {}
}
}
resource "google_secret_manager_secret_version" "db_host_v" {
  secret = google_secret_manager_secret.db_host.id
  secret_data = "/cloudsql/${google_sql_database_instance.postgres.connection_name}"
}

resource "google_secret_manager_secret" "db_user" {
  secret_id = "db_user"
  replication {
  auto {}
}
}
resource "google_secret_manager_secret_version" "db_user_v" {
  secret = google_secret_manager_secret.db_user.id
  secret_data = "alerting_user"
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "db_password"
  replication {
  auto {}
}
}
resource "google_secret_manager_secret_version" "db_password_v" {
  secret = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_secret_manager_secret" "db_name" {
  secret_id = "db_name"
  replication {
  auto {}
}
}
resource "google_secret_manager_secret_version" "db_name_v" {
  secret = google_secret_manager_secret.db_name.id
  secret_data = "alerting"
}

resource "google_secret_manager_secret" "smtp_username" {
  secret_id = "smtp_username"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "smtp_username_v" {
  secret      = google_secret_manager_secret.smtp_username.id
  secret_data = var.smtp_from
}

resource "google_secret_manager_secret" "smtp_host" {
  secret_id = "smtp_host"
  replication {
  auto {}
}
}

resource "google_secret_manager_secret_version" "smtp_host_v" {
  secret      = google_secret_manager_secret.smtp_host.id
  secret_data = "smtp.mailersend.net"
}

resource "google_secret_manager_secret" "smtp_port" {
  secret_id = "smtp_port"
  replication {
  auto {}
}
}

resource "google_secret_manager_secret_version" "smtp_port_v" {
  secret      = google_secret_manager_secret.smtp_port.id
  secret_data = "587"
}

resource "google_secret_manager_secret" "smtp_from" {
  secret_id = "smtp_from"
  replication {
  auto {}
}
}

resource "google_secret_manager_secret_version" "smtp_from_v" {
  secret      = google_secret_manager_secret.smtp_from.id
  secret_data = var.smtp_from
}

resource "google_secret_manager_secret" "smtp_password" {
  secret_id = "smtp_password"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "smtp_password_v" {
  secret      = google_secret_manager_secret.smtp_password.id
  secret_data = var.smtp_password
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

# Create the secret in Secret Manager
resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "jwt_secret"
  replication {
    auto {}
  }
}

# Store the generated secret in Secret Manager
resource "google_secret_manager_secret_version" "jwt_secret_version" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = random_password.jwt_secret.result
}
