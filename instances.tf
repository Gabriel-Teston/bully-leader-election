resource "google_compute_instance_template" "vm_instance_template" {
  name         = "terraform-instance-template"
  machine_type = "e2-micro"

  disk {
    source_image = "ubuntu-os-cloud/ubuntu-minimal-2004-lts"
  }

  metadata_startup_script =  file("./startup.sh")

  network_interface {
    network = google_compute_network.vpc_network.name
    access_config {
    }
  }
}

resource "google_compute_instance_group_manager" "bully" {
  name = "bully-igm"

  base_instance_name = "bully"

  version {
    instance_template  = google_compute_instance_template.vm_instance_template.id
  }

  wait_for_instances = true

  target_size  = 6

}