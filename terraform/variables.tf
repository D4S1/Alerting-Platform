
variable "project_id" {}
variable "region" { default = "europe-central2" }

variable "api_image" {}
variable "monitoring_image" {}
variable "notification_image" {}
variable "ui_image" {}

variable "smtp_password" {
  type      = string
  sensitive = true
}

