
resource "google_sql_database_instance" "postgres" {
  name = "alerting-postgres"
  database_version = "POSTGRES_15"
  region = var.region
  settings { tier = "db-f1-micro" }
  deletion_protection = false
}

resource "google_sql_database" "db" {
  name = "alerting"
  instance = google_sql_database_instance.postgres.name
}

resource "random_password" "db_password" {
  length = 20
  special = true
}

resource "google_sql_user" "user" {
  name = "alerting_user"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}
