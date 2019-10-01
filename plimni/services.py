import re

from plimni.tags import Tags


class Service():
    """
    A service represents an exposed endpoint for the outside world.
    Plimni can loadbalance both HTTP(S) APIs and simple TCP endpoints.

    Args:
        cluster_branch (str): The main branch this cluster operates on.
        cluster_domain (str): The domain of this cluster.
        expose (bool): Whether to expose the endpoint or not. This allows you
                       to quickly disable an endpoint by changing the service
                       annotation / tags without having to actually remove the
                       backends. Defaults to `False`.
        name (str): The name of the service.
        branch (str): The branch of the service. Defaults to `master`.
        fqdn (str): The FQDN Plimni has to answer to. Only available in `http`
                    or `https` modes.
        additional_fqdns ([]str): A list of additional FQDN Plimni will answer
                                  to. Only available in `http` or `https`
                                  modes.
        mode (str): `http` for HTTP-only or `https` for both HTTP and HTTPS.
        http_port (int): The port to listen to for HTTP requests (defaults to
                         80).
        https_port (int): The port to listen to for HTTPS requests (defaults to
                          443).
        http_sanitize_codes ([]str): The codes to catch before they are sent
                                     back to clients. These codes will be
                                     replaced by the value of
                                     `http_sanitize_return`.
        http_sanitize_return (str): The code to send back instead of those
                                    catched.
        backends ([]tuple): A list (ip,port) couples of backends for this
                            service.
    """
    STR_REGEX = re.compile(r"^[a-zA-Z0-9-_.]+$")
    CODES_REGEX = re.compile(r"^[1-5][0-9]{2}$")

    def __init__(self, cluster_branch, cluster_domain, expose, name,
                 branch, fqdn, additional_fqdns, mode, http_port, https_port,
                 http_sanitize_codes, http_sanitize_return, backends,
                 ):
        # Clean data
        expose = False if expose is None else (
            True if expose.lower() == "true" else False
        )
        branch = "master" if branch is None else branch
        fqdn = "" if fqdn is None else fqdn
        additional_fqdns = [] if additional_fqdns is None else additional_fqdns
        mode = "https" if mode is None else mode
        http_port = 80 if http_port is None else int(http_port)
        https_port = 443 if https_port is None else int(https_port)
        http_sanitize_codes = [] if http_sanitize_codes is None\
            else http_sanitize_codes
        http_sanitize_return = "" if http_sanitize_return is None\
            else http_sanitize_return
        backends = [] if backends is None else backends

        # Check and process data
        self.expose = expose

        if not name:
            raise ValueError("The name must be set")

        self.name = name

        self.additional_fqdns = additional_fqdns

        if self.additional_fqdns:
            for f in self.additional_fqdns:
                if not Service.STR_REGEX.search(f):
                    raise ValueError("{} is not valid (only alphanumeric "
                                     "characters and dash, underscore and dot "
                                     "are allowed"
                                     "".format(Tags.ADDITIONAL_FQDNS))

        if fqdn:
            if not Service.STR_REGEX.search(fqdn):
                raise ValueError("`fqdn` is not valid (only alphanumeric "
                                 "characters and dash, underscore and dot are "
                                 "allowed")
            self.fqdn = fqdn
        else:
            self.branch = branch
            # Normalize branch name (replace all special characters with "-")
            self.branch_normalized = re.sub(r"[^a-zA-Z0-9_.-]+", "-", branch)

            self.fqdn = "{}.{}.{}".format(
                self.name, self.branch_normalized, cluster_domain
            )

            if self.branch == cluster_branch:
                self.additional_fqdns.append(self.name + "." + cluster_domain)

        self.mode = mode

        if mode == "http":
            self.http_port = http_port
        elif mode == "https":
            self.https_port = https_port
        else:
            raise ValueError("The mode must be one of http or https")

        # Boolean used to know if we're sanitizing this service
        self.sanitizes = False

        if http_sanitize_codes:
            if not http_sanitize_return:
                raise ValueError("You have to provide the sanitized value if "
                                 "you want to sanitize codes")

            if not Service.CODES_REGEX.search(http_sanitize_return):
                raise ValueError("The sanitized return code {} is not valid"
                                 "".format(http_sanitize_return))

            for code in http_sanitize_codes:
                if not Service.CODES_REGEX.search(code):
                    raise ValueError("The code {} to sanitize is not valid"
                                     "".format(code))

            self.sanitizes = True
            self.http_sanitize_codes = http_sanitize_codes
            self.http_sanitize_return = http_sanitize_return

        self.backends = backends
