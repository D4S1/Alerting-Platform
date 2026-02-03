variable "project_id" {
  type = string
  # default = "irio-alerting"
}

variable "region" {
  type    = string
  default = "europe-central2"
}

variable "api_image" {}
variable "monitoring_image" {}
variable "notification_image" {}
variable "ui_image" {}

variable "smtp_password" {
  type      = string
  sensitive = true
}

variable "smtp_from" {
  type      = string
  sensitive = true
}