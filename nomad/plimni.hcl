job "plimni" {
	constraint {
		attribute = "${meta.type}"
		value     = "lb"
	}

	datacenters = ["main"]

	type = "service"

	group "plimni" {
		count = 1

		task "haproxy" {
			driver = "docker"

			config {
				image = "haproxy:2.0.6"
				args = ["bash", "-c", "touch ${HAP_SRV_CONF} && haproxy -f ${NOMAD_TASK_DIR}/haproxy.cfg -f ${HAP_SRV_CONF}"]
				network_mode = "host"
				pid_mode = "host"

				# HAProxy will probably need to handle a lot of connections
				sysctl {
					net.core.somaxconn = "16384"
				}

				volumes = [
					"/volumes/certs/:/certs",
				]
			}

			env {
				HAP_SRV_CONF = "${NOMAD_ALLOC_DIR}/data/haproxy-services.cfg"
			}

			template {
				destination = "local/haproxy.cfg"
				change_mode = "signal"
				change_signal = "SIGUSR2"
				data = <<EOF
global
	log stderr format rfc5424 local0 info
	master-worker
	pidfile {{ env "NOMAD_ALLOC_DIR" }}/data/haproxy.pid
	maxconn 50000
	nbthread 2
	stats socket {{ env "NOMAD_ALLOC_DIR" }}/data/stats.sock mode 666 level admin
	# Enforce strong algorithms
	ssl-default-bind-ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256
	ssl-default-bind-options no-sslv3 no-tlsv10 no-tlsv11 no-tls-tickets
	ssl-default-server-ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256
	ssl-default-server-options no-sslv3 no-tlsv10 no-tlsv11 no-tls-tickets
defaults
	log global
EOF
			}

			resources {
				cpu = 1000
				memory = 500
			}
		}

		task "plimni" {
			driver = "docker"

			config {
				image = "akaoj/plimni:latest"
				args = [
					"python3", "-m", "plimni",
					"--orchestrator", "nomad",
					"--cluster-domain", "${env["CLUSTER_DOMAIN"]}",
					"--cluster-email", "${env["CLUSTER_EMAIL"]}",
					"--cluster-branch", "${env["CLUSTER_BRANCH"]}",
					"--private-ip", "${env["PRIVATE_IP"]}",
					"--sleep-time", "${env["SLEEP_TIME"]}",
					"--haproxy-services-conf-file", "${NOMAD_ALLOC_DIR}/data/haproxy-services.cfg",
					"--haproxy-pid-file", "${NOMAD_ALLOC_DIR}/data/haproxy.pid",
					"--haproxy-sanitize-conf-folder", "${NOMAD_ALLOC_DIR}/data/sanitize.d",
					"--certbot-conf-folder", "/certs",
				]
				network_mode = "host"
				pid_mode = "host"
				volumes = [
					"/volumes/certs/:/certs",
				]
			}

			# XXX You have to configure at least these variables
			env {
				CLUSTER_DOMAIN = ""  # Set a domain which resolves to your cluster
				CLUSTER_EMAIL = ""  # Set the email Certbot will register with
				CLUSTER_BRANCH = "master"  # Set the branch Plimni will use for aliases
				PRIVATE_IP = ""  # Set the private IP of your loadbalancer (Nomad only)
				SLEEP_TIME = "5"  # You can change the "responsiveness" of Plimni with this value
			}
			# XXX Thanks

			resources {
				cpu = 100
				memory = 100
			}
		}
	}
}
