job "plimni-certbot" {
	constraint {
		attribute = "${meta.type}"
		value     = "lb"
	}

	datacenters = ["main"]

	type = "batch"

	periodic {
		cron = "* * * * * *"
		prohibit_overlap = true
	}

	group "certbot-plimni" {
		count = 1

		task "certbot" {
			driver = "docker"

			config {
				image = "certbot/certbot:v0.31.0"
				args = ["certonly", "-c", "/etc/letsencrypt/cli.ini"]
				volumes = [
					"/volumes/certs/:/etc/letsencrypt/",
				]
				port_map {
					http = 80
				}
			}

			service {
				name = "plimni-certbot"
				port = "http"
			}

			resources {
				cpu = 100
				memory = 100
				network {
					port "http" {
						static = "8080"
					}
				}
			}
		}
	}
}
