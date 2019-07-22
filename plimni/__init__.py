# This script will retrieve all services in the cluster and add them as
# frontends in HAProxy configuration so HAProxy will be able to serve them from
# Internet.
# A service will be exposed at the following URL:
#   <service>.<branch>.<cluster_domain>
# i.e.:
#   blog.master.mydomain.com
#
# If you need to expose a service with a completely different domain than your
# cluster domain, you can directly specify the FQDN to expose and HAProxy will
# respond to requests for this domain as well.
#
# In any case, don't forget to route either your `cluster_domain` or `fqdn` to
# your loadbalancer's IP.
#
# See the documentations for required annotations / tags depending on your
# cluster type.

import os
import signal
import sys
import time

import plimni.clients
import plimni.configuration
import plimni.services


def reload_haproxy(pid_file: str) -> int:
    """
    Send a SIGUSR2 to HAProxy to make it reload its configuration.
    """
    if not os.path.isfile(pid_file):
        raise ValueError("The HAProxy PID file {} does not exist; can't "
                         "reload HAProxy".format(pid_file))

    pid = 0

    with open(pid_file, "r") as _pid_file:
        pid = int(_pid_file.read())

    if pid == 0:
        raise ValueError("Can't retrieve HAProxy PID from file {}; can't "
                         "reload HAProxy".format(pid_file))

    os.kill(pid, signal.SIGUSR2)

    return pid


def main(orchestrator: str, cluster_domain: str, cluster_email: str,
         cluster_branch: str, private_ip: str, init: bool, sleep_time: int,
         haproxy_services_conf_file: str, haproxy_pid_file: str,
         haproxy_sanitize_conf_folder: str, certbot_conf_folder: str):
    print("Starting plimni")

    client = plimni.clients.get_client(orchestrator)

    certbot_url = client.get_certbot_url(private_ip)

    while True:
        services = client.get_services(
            cluster_branch=cluster_branch,
            cluster_domain=cluster_domain,
        )

        configuration = plimni.configuration.Configuration(
            haproxy_services_conf_file=haproxy_services_conf_file,
            haproxy_sanitize_conf_folder=haproxy_sanitize_conf_folder,
            certbot_conf_folder=certbot_conf_folder,
            cluster_domain=cluster_domain,
            cluster_email=cluster_email,
            cluster_branch=cluster_branch,
            services=services,
            certbot_url=certbot_url,
        )

        haproxy_changed = configuration.haproxy_changed()
        sanitize_changed = configuration.sanitize_changed()

        if haproxy_changed:
            print("HAProxy configuration changed, writing the new one")
            configuration.haproxy_write()

        if sanitize_changed:
            print("Sanitized values changed, writing new ones")
            configuration.sanitize_write()

        if configuration.certbot_changed():
            print("Certbot configuration changed, writing the new one")
            configuration.certbot_write()

        if init:
            print("End of init mode, exiting")
            return

        if haproxy_changed or sanitize_changed:
            print("Reloading HAProxy")

            try:
                hap_pid = reload_haproxy(haproxy_pid_file)
                print("Reloaded HAProxy master process PID {}".format(hap_pid))
            except Exception as exc:
                print("Error when reloading HAProxy: {}".format(str(exc)))

        print("All done, sleeping {} seconds".format(sleep_time))
        time.sleep(sleep_time)
