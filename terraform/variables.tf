variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "europe-central2"
}

variable "api_image" {
  type    = string
  default = "europe-central2-docker.pkg.dev/irio-alerting/irio-alerting-dockers/api:v1.0.0"
}

variable "monitoring_image" {
  type    = string
  default = "europe-central2-docker.pkg.dev/irio-alerting/irio-alerting-dockers/monitoring:v1.0.0"
}

variable "notification_image" {
  type    = string
  default = "europe-central2-docker.pkg.dev/irio-alerting/irio-alerting-dockers/notification:v1.0.0"
}

variable "ui_image" {
  type    = string
  default = "europe-central2-docker.pkg.dev/irio-alerting/irio-alerting-dockers/ui:v1.0.0"
}
