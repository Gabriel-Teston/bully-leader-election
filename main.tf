terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "3.73.0"
    }
  }

  required_version = ">= 0.15.0"
}

provider "google" {
  project = var.project
  region  = var.region
  zone    = var.zone
}

module "project_services" {
  source  = "terraform-google-modules/project-factory/google//modules/project_services"
  version = "3.3.0"

  project_id = var.project

  activate_apis = [
    "compute.googleapis.com",
    "oslogin.googleapis.com"
  ]

  disable_services_on_destroy = false
  disable_dependent_services  = false
}