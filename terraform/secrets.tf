resource "google_secret_manager_secret" "db_url" {
  secret_id = "db_url"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_url_v" {
  secret = google_secret_manager_secret.db_url.id

  secret_data = format(
    "postgresql+psycopg2://%s:%s@/%s?host=/cloudsql/%s",
    urlencode(google_sql_user.user.name),
    urlencode(random_password.db_password.result),
    urlencode(google_sql_database.db.name),
    google_sql_database_instance.postgres.connection_name
  )
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
resource "google_secret_manager_secret_version" "jwt_secret_v" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = random_password.jwt_secret.result
}
