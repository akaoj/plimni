from consul import Consul

from .clients import Client
from .configuration import PREFIX, Tags
from .services import Service


class NomadClient(Client):
    def __init__(self, instance: Consul):
        self._instance = instance

    def get_services(self, cluster_branch: str, cluster_domain: str):
        _, services = self._instance.catalog.services()

        print("Retrieving services on Consul...")

        services_computed = []

        # Filter the services
        for service_name, service_tags in services.items():
            print("Processing service {}...".format(service_name))

            if not service_tags:
                print("=> no tags, skipping it")
                continue

            # Skip if there is no Plimni-specific annotation
            if not any(
                    key.startswith(PREFIX) for key in service_tags
            ):
                print("=> no {} tags, skipping it".format(PREFIX))
                continue

            tags = {
                key: value
                for key, value in
                map(
                    lambda e: e.split("="),
                    filter(lambda e: e.startswith(PREFIX), service_tags)
                )
            }

            s_expose = tags.get(Tags.EXPOSE)
            s_name = tags.get(Tags.NAME)
            s_branch = tags.get(Tags.BRANCH)
            s_fqdn = tags.get(Tags.FQDN)
            s_mode = tags.get(Tags.MODE)
            s_http_port = tags.get(Tags.HTTP_PORT)
            s_https_port = tags.get(Tags.HTTPS_PORT)
            s_http_sanitize_codes = tags.get(Tags.HTTP_SANITIZE_CODES)
            if s_http_sanitize_codes is not None:
                s_http_sanitize_codes = s_http_sanitize_codes.split(",")
            s_http_sanitize_return = tags.get(Tags.HTTP_SANITIZE_RETURN)

            # If no annotation is defined for the name, use the service name
            if not s_name:
                s_name = service_name

            # Retrieve backends
            print("Tags processed, retrieving endpoints...")

            _, endpoints = self._instance.catalog.service(service_name)

            s_backends = map(
                lambda e: (e.get("Address"), e.get("ServicePort")),
                endpoints
            )

            plimni_service = None

            try:
                plimni_service = Service(
                    cluster_branch=cluster_branch,
                    cluster_domain=cluster_domain,
                    expose=s_expose,
                    name=s_name,
                    branch=s_branch,
                    fqdn=s_fqdn,
                    mode=s_mode,
                    http_port=s_http_port,
                    https_port=s_https_port,
                    http_sanitize_codes=s_http_sanitize_codes,
                    http_sanitize_return=s_http_sanitize_return,
                    backends=s_backends,
                )
            except ValueError as err:
                print("Can't process service {} because of: {}"
                      "".format(service_name, str(err)))
                continue

            services_computed.append(plimni_service)

        return services_computed

    def get_certbot_url(self, private_ip: str) -> str:
        return "{}:8080".format(private_ip)


def get_client() -> Client:
    return NomadClient(Consul())
