import hashlib
import os
import typing

import jinja2

import plimni.services


PREFIX = "plimni.io"


class Tags():
    EXPOSE = "{}/expose".format(PREFIX)
    BRANCH = "{}/branch".format(PREFIX)
    NAME = "{}/name".format(PREFIX)
    FQDN = "{}/fqdn".format(PREFIX)
    MODE = "{}/mode".format(PREFIX)
    HTTP_PORT = "{}/http-port".format(PREFIX)
    HTTPS_PORT = "{}/https-port".format(PREFIX)
    HTTP_SANITIZE_CODES = "{}/http-sanitize-codes".format(PREFIX)
    HTTP_SANITIZE_RETURN = "{}/http-sanitize-return".format(PREFIX)


class Configuration():
    HAPROXY_TEMPLATE = "./plimni/templates/haproxy.cfg.j2"
    SANITIZE_TEMPLATE = "./plimni/templates/haproxy_sanitize_return.http.j2"
    CERTBOT_TEMPLATE = "./plimni/templates/certbot.ini.j2"

    def __init__(self, haproxy_services_conf_file: str,
                 haproxy_sanitize_conf_folder: str, certbot_conf_folder: str,
                 cluster_domain: str,
                 cluster_email: str,
                 cluster_branch: str,
                 services: typing.List[plimni.services.Service],
                 certbot_url: str):
        self.haproxy_conf_file = haproxy_services_conf_file
        self.sanitize_conf_folder = haproxy_sanitize_conf_folder
        self.certbot_conf_file = "{}/cli.ini".format(certbot_conf_folder)
        self.https_cert_file = ("{}/live/{}/bundle.pem"
                                "".format(certbot_conf_folder, cluster_domain))

        if not cluster_email:
            cluster_email = "postmaster@{}".format(cluster_domain)

        self.cluster_email = cluster_email

        self._services = services

        # Parse the services and generate the configuration files
        self._haproxy_conf = Configuration._generate_haproxy_conf(
            services=self._services,
            https_cert_file=self.https_cert_file,
            sanitize_conf_folder=self.sanitize_conf_folder,
            cluster_domain=cluster_domain,
            cluster_branch=cluster_branch,
            certbot_url=certbot_url,
        )
        self._sanitize_confs = Configuration._generate_sanitize_confs(services)
        self._certbot_conf = Configuration._generate_certbot_conf(
            services=self._services,
            cluster_domain=cluster_domain,
            cluster_email=cluster_email,
            cluster_branch=cluster_branch,
        )

    @staticmethod
    def _generate_haproxy_conf(
            services: typing.List[plimni.services.Service],
            https_cert_file: str,
            sanitize_conf_folder: str,
            cluster_domain: str,
            cluster_branch: str,
            certbot_url: str,
    ) -> str:
        with open(Configuration.HAPROXY_TEMPLATE, "r") as tmpl:
            template = jinja2.Template(tmpl.read())

        return template.render(
            services=services,
            https_cert_file=("" if not os.path.isfile(https_cert_file)
                             else https_cert_file),
            sanitize_conf_folder=sanitize_conf_folder,
            cluster_domain=cluster_domain,
            cluster_branch=cluster_branch,
            certbot_url=certbot_url,
        )

    @staticmethod
    def _generate_sanitize_confs(
            services: typing.List[plimni.services.Service],
    ) -> typing.Dict[str, str]:
        with open(Configuration.SANITIZE_TEMPLATE, "r") as tmpl:
            template = jinja2.Template(tmpl.read())

        configs = {}

        for svc in services:
            if not svc.sanitizes:
                continue

            # We always return the same sanitized return code
            rendered = template.render(svc.http_sanitize_return)

            for code in svc.http_sanitize_codes:
                configs[svc.fqdn + "-" + code] = rendered

        return configs

    @staticmethod
    def _generate_certbot_conf(
            services: typing.List[plimni.services.Service],
            cluster_domain: str,
            cluster_email: str,
            cluster_branch: str,
    ) -> str:
        with open(Configuration.CERTBOT_TEMPLATE, "r") as tmpl:
            template = jinja2.Template(tmpl.read())

        return template.render(
            services=services,
            cluster_domain=cluster_domain,
            cluster_email=cluster_email,
            cluster_branch=cluster_branch,
        )

    @staticmethod
    def _has_changed(file_path: str, content: str) -> bool:
        if not os.path.isfile(file_path):
            if not content:
                return False
            return True

        new_hash = hashlib.blake2b(content.encode("utf-8")).hexdigest()

        with open(file_path, "r") as file_:
            old_hash = hashlib\
                .blake2b(file_.read().encode("utf-8"))\
                .hexdigest()

        return old_hash != new_hash

    def haproxy_changed(self) -> bool:
        return Configuration._has_changed(
            file_path=self.haproxy_conf_file,
            content=self._haproxy_conf,
        )

    def sanitize_changed(self) -> bool:
        for file_name, content in self._sanitize_confs.items():
            changed = Configuration._has_changed(
                file_path="{}/{}.html".format(self.sanitize_conf_folder,
                                              file_name),
                content=content,
            )

            if changed:
                return True

        return False

    def certbot_changed(self) -> bool:
        return Configuration._has_changed(
            file_path=self.certbot_conf_file,
            content=self._certbot_conf,
        )

    def haproxy_write(self):
        with open(self.haproxy_conf_file, "w") as file_:
            file_.write(self._haproxy_conf)

    def sanitize_write(self):
        for name, content in self._sanitize_confs.items():
            file_path = "{}/{}.html".format(self.sanitize_conf_folder, name)
            with open(file_path, "w") as file_:
                file_.write(content)

    def certbot_write(self):
        with open(self.certbot_conf_file, "w") as file_:
            file_.write(self._certbot_conf)
