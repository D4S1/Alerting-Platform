
variable "project_id" {}
variable "region" { default = "europe-central2" }

variable "api_image" {}
variable "monitoring_image" {}
variable "notification_image" {}
variable "ui_image" {}

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

