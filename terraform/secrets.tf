
resource "google_secret_manager_secret" "db_host" {
  secret_id = "DB_HOST"
  replication { auto {} }
}
resource "google_secret_manager_secret_version" "db_host_v" {
  secret = google_secret_manager_secret.db_host.id
  secret_data = google_sql_database_instance.postgres.connection_name
}

resource "google_secret_manager_secret" "db_user" {
  secret_id = "DB_USER"
  replication { auto {} }
}
resource "google_secret_manager_secret_version" "db_user_v" {
  secret = google_secret_manager_secret.db_user.id
  secret_data = "alerting_user"
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "DB_PASSWORD"
  replication { auto {} }
}
resource "google_secret_manager_secret_version" "db_password_v" {
  secret = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_secret_manager_secret" "db_name" {
  secret_id = "DB_NAME"
  replication { auto {} }
}
resource "google_secret_manager_secret_version" "db_name_v" {
  secret = google_secret_manager_secret.db_name.id
  secret_data = "alerting"
}
