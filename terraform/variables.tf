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

variable "smtp_username" {
  type      = string
  sensitive = true
}

variable "smtp_password" {
  type      = string
  sensitive = true
}

variable "jwt_secret" {
  type      = string
  sensitive = true
}

variable "smtp_host" {
  type    = string
  default = "smtp.gmail.com"
}

variable "smtp_port" {
  type    = number
  default = 587
}

variable "smtp_from" {
  type = string
}

variable "jwt_exp_minutes" {
  type    = number
  default = 15
}

variable "escalation_delay_seconds" {
  type    = number
  default = 300
}

