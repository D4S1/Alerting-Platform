variable "project_id" {
  type = string
  default = "irio-alerting"
}

variable "region" {
  type    = string
  default = "europe-central2"
}

variable "api_image" {
  default = "europe-central2-docker.pkg.dev/irio-alerting/irio-alerting-dockers/api:v1.0.1"
}
variable "monitoring_image" {
  default = "europe-central2-docker.pkg.dev/irio-alerting/irio-alerting-dockers/monitoring:v1.0.1"
}
variable "notification_image" {
  default = "europe-central2-docker.pkg.dev/irio-alerting/irio-alerting-dockers/notification:v1.0.1"
}
variable "ui_image" {
  default = "europe-central2-docker.pkg.dev/irio-alerting/irio-alerting-dockers/ui:v1.0.1"
}

variable "db_image" {
  default = "europe-central2-docker.pkg.dev/irio-alerting/irio-alerting-dockers/db_init:v1.0.0"
}

variable "smtp_password" {
  type      = string
  sensitive = true
}

variable "smtp_from" {
  type      = string
  sensitive = true
}
