from kubernetes import client, config

from .clients import Client
from .configuration import PREFIX, Tags
from .services import Service


class KubernetesClient(Client):
    def __init__(self, instance: client):
        self._instance = instance

    def get_services(self, cluster_branch: str, cluster_domain: str):
        services = self._instance.list_namespaced_service(namespace="default")

        print("Retrieving services on Kubernetes...")

        services_computed = []

        # Filter the services
        for service in services.items:
            service_name = service.metadata.name
            annotations = service.metadata.annotations

            print("Processing service {}...".format(service_name))

            if annotations is None:
                print("=> no annotation, skipping it")
                continue

            # Skip if there is no Plimni-specific annotation
            if not any(
                    key.startswith(PREFIX) for key in annotations.keys()
            ):
                print("=> no {} annotation, skipping it".format(PREFIX))
                continue

            s_expose = annotations.get(Tags.EXPOSE)
            s_name = service_name
            s_branch = annotations.get(Tags.BRANCH)
            s_fqdn = annotations.get(Tags.FQDN)
            s_mode = annotations.get(Tags.MODE)
            s_http_port = annotations.get(Tags.HTTP_PORT)
            s_https_port = annotations.get(Tags.HTTPS_PORT)
            s_http_sanitize_codes = annotations.get(Tags.HTTP_SANITIZE_CODES)
            if s_http_sanitize_codes is not None:
                s_http_sanitize_codes = s_http_sanitize_codes.split(",")
            s_http_sanitize_return = annotations.get(Tags.HTTP_SANITIZE_RETURN)

            # Retrieve backends
            print("Annotations processed, retrieving endpoints...")

            endpoint = self._instance.read_namespaced_endpoints(
                name=s_name,
                namespace="default",
            )

            s_backends = []

            if endpoint.subsets is not None:
                # XXX this might cause issues in the future if we have
                # multiple subsets but it's not well understood as of now
                subset = endpoint.subsets[0]

                # XXX same as above but if we have multiple ports for a service
                port = subset.ports[0].port

                if subset.addresses:
                    for ip_addr in subset.addresses:
                        print("Adding backend {}:{}".format(ip_addr, port))
                        s_backends.append((ip_addr, port))

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
        return "_http._tcp.certbot.loadbalancer.svc.cluster.local"


def get_client() -> Client:
    config.load_incluster_config()
    return KubernetesClient(client.CoreV1Api())
