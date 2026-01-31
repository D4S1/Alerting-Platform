
resource "google_secret_manager_secret" "db_host" {
  secret_id = "DB_HOST"
  replication {
  auto {}
}
}
resource "google_secret_manager_secret_version" "db_host_v" {
  secret = google_secret_manager_secret.db_host.id
  secret_data = "/cloudsql/${google_sql_database_instance.postgres.connection_name}"
}

resource "google_secret_manager_secret" "db_user" {
  secret_id = "DB_USER"
  replication {
  auto {}
}
}
resource "google_secret_manager_secret_version" "db_user_v" {
  secret = google_secret_manager_secret.db_user.id
  secret_data = "alerting_user"
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "DB_PASSWORD"
  replication {
  auto {}
}
}
resource "google_secret_manager_secret_version" "db_password_v" {
  secret = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_secret_manager_secret" "db_name" {
  secret_id = "DB_NAME"
  replication {
  auto {}
}
}
resource "google_secret_manager_secret_version" "db_name_v" {
  secret = google_secret_manager_secret.db_name.id
  secret_data = "alerting"
}

resource "google_secret_manager_secret" "smtp_username" {
  secret_id = "SMTP_USERNAME"
  replication { auto {} }
}

resource "google_secret_manager_secret_version" "smtp_username_v" {
  secret      = google_secret_manager_secret.smtp_username.id
  secret_data = "MS_vpJOU2@test-y7zpl983od545vx6.mlsender.net"
}

resource "google_secret_manager_secret" "smtp_host" {
  secret_id = "SMTP_HOST"
  replication { auto {} }
}

resource "google_secret_manager_secret_version" "smtp_host_v" {
  secret      = google_secret_manager_secret.smtp_host.id
  secret_data = "smtp.mailersend.net"
}

resource "google_secret_manager_secret" "smtp_port" {
  secret_id = "SMTP_PORT"
  replication { auto {} }
}

resource "google_secret_manager_secret_version" "smtp_port_v" {
  secret      = google_secret_manager_secret.smtp_port.id
  secret_data = "587"
}

resource "google_secret_manager_secret" "smtp_from" {
  secret_id = "SMTP_FROM"
  replication { auto {} }
}

resource "google_secret_manager_secret_version" "smtp_from_v" {
  secret      = google_secret_manager_secret.smtp_from.id
  secret_data = "MS_vpJOU2@test-y7zpl983od545vx6.mlsender.net"
}

resource "google_secret_manager_secret" "smtp_password" {
  secret_id = "SMTP_PASSWORD"
  replication { auto {} }
}

resource "google_secret_manager_secret_version" "smtp_password_v" {
  secret      = google_secret_manager_secret.smtp_password.id
  secret_data = var.smtp_password
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "JWT_SECRET"
  replication { auto {} }
}

resource "google_secret_manager_secret_version" "jwt_secret_v" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = var.jwt_secret
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

resource "google_secret_manager_secret_version" "jwt_secret_v" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = random_password.jwt_secret.result
}

