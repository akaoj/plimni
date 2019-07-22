#!/usr/bin/env python3

import argparse
import os
import sys

from . import main


parser = argparse.ArgumentParser("plimni")

parser.add_argument(
    "-o", "--orchestrator",
    required=True,
    choices=["k8s", "nomad"],
    help="The orchestrator Plimni runs on",
)

parser.add_argument(
    "-d", "--cluster-domain",
    required=True,
    help="Your cluster domain",
)

parser.add_argument(
    "-e", "--cluster-email",
    help="Your cluster default email address",
)

parser.add_argument(
    "-b", "--cluster-branch",
    default="master",
    help="The main branch on your cluster",
)

parser.add_argument(
    "--private-ip",
    help="Your loadbalancer private IP (Nomad only, required)",
)

parser.add_argument(
    "--init",
    default=False,
    const=True,
    nargs="?",
    help=("Whether to run Plimni in init mode (generate the configuration "
          "and exit, don't daemonize"),
)

parser.add_argument(
    "-t", "--sleep-time",
    type=int,
    default=5,
    help="The time Plimni will wait between runs",
)

parser.add_argument(
    "--haproxy-services-conf-file",
    default="/usr/local/etc/haproxy/conf.d/services.cfg",
    help="The HAProxy services configuration file to manage",
)
parser.add_argument(
    "--haproxy-pid-file",
    default="/usr/local/etc/haproxy/conf.d/haproxy.pid",
    help="The HAProxy PID file to know which process to reload",
)
parser.add_argument(
    "--haproxy-sanitize-conf-folder",
    default="/usr/local/etc/haproxy/sanitize.d",
    help="The HAProxy sanitized returns folder to manage",
)
parser.add_argument(
    "--certbot-conf-folder",
    default="/usr/local/etc/haproxy/certs",
    help="The Certbot configuration folder to manage",
)

args = parser.parse_args()

if not args.orchestrator:
    parser.print_help(sys.stderr)
    sys.exit(1)

if not args.cluster_domain:
    parser.print_help(sys.stderr)
    sys.exit(1)

if not os.path.isdir(args.haproxy_sanitize_conf_folder):
    os.mkdir(args.haproxy_sanitize_conf_folder)

if args.orchestrator == "nomad" and not args.private_ip:
    parser.print_help(sys.stderr)
    sys.exit(1)


main(
    orchestrator=args.orchestrator,
    cluster_domain=args.cluster_domain,
    cluster_email=args.cluster_email,
    cluster_branch=args.cluster_branch,
    private_ip=args.private_ip,
    init=args.init,
    sleep_time=args.sleep_time,
    haproxy_services_conf_file=args.haproxy_services_conf_file,
    haproxy_pid_file=args.haproxy_pid_file,
    haproxy_sanitize_conf_folder=args.haproxy_sanitize_conf_folder,
    certbot_conf_folder=args.certbot_conf_folder
)
