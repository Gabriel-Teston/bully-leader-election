data "google_compute_instance_group" "bully" {
    self_link = "${google_compute_instance_group_manager.bully.instance_group}"
}

output "instances" {
    value = [for x in data.google_compute_instance_group.bully.instances : split("/", x)[length(split("/", x)) - 1]]
}

resource "google_compute_project_metadata" "default" {
    metadata = tomap({for x in data.google_compute_instance_group.bully.instances : split("/", x)[length(split("/", x)) - 1] => split("/", x)[length(split("/", x)) - 1]})
} 