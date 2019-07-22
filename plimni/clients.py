import typing

from .services import Service


class Client():
    def get_services(
            self, cluster_branch: str, cluster_domain: str,
    ) -> typing.List[Service]:
        """"Retrieve environment from cluster and build a Services list."""
        raise NotImplementedError()

    def get_certbot_url(self, private_ip: str) -> str:
        """Return the Certbot URL for the given cluster."""
        raise NotImplementedError()


def get_client(name: str) -> Client:
    if name == "k8s":
        from . import k8s
        return k8s.get_client()
    if name == "nomad":
        from . import nomad
        return nomad.get_client()
    else:
        raise NotImplementedError("The orchestrator {} is not implemented"
                                  "".format(name))
