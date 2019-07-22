![Docker build](https://img.shields.io/docker/cloud/build/akaoj/plimni.svg?style=flat-square)

# Plimni

**Plimni** is a on-premise (cloud or baremetal) loadbalancer for **Kubernetes** and **Nomad** clusters. It allows you
to expose your cluster's internal services to the world.

As of now, it can only route layers 6/7 (HTTP / HTTPS) traffic, but it's expected to handle layer 2 (TCP / UDP) traffic
ultimately. It also natively handles HTTPS.

Plimni leverages the power of existing, renowned, production-safe tools to offer a complete solution: it uses
[HAProxy](https://www.haproxy.org/) for loadbalancing, [Certbot](https://certbot.eff.org/) for certificate issuance and
[HAProxy Exporter for Prometheus](https://github.com/prometheus/haproxy_exporter) to supply metrics (Kubernetes only
for the moment).

In its core, Plimni is simply a small glue which will bind all these tools together to help you expose easily your
micro-services to the world.


# Features

## Automatic service discovery and automatic exposure to the Internet

Plimni will look for the running services in the cluster and automatically expose those who are configured to by
generating a reachable URL for each and every service. These URLs look like:

`<name>.<branch>.<cluster_domain>`

- `<name>` is the name of your service
- `<branch>` is the branch your service is on (see [Service configuration](#service-configuration))
- `<branch>` is the main domain of your cluster

If your service is on the same branch as the cluster main branch, your service will also be available on the URL:

`<name>.<cluster_domain>`

This allows you to spawn on the same cluster multiple branches of the same project and be able to test your different
features easily with an URL easy to remember.


### About cluster domain and cluster main branch

For Plimni to be able to automatically generate URLs for your services, it has to know the domain which resolves to
the current cluster.

For example, let's say your cluster domain is `mydomain.com` and this domain resolves to your loadbalancer. Plimni will
use this domain name to create the URLs of your services: if you deploy a `blog` service on the `master` branch, Plimni
will automatically route `blog.master.mydomain.com` to the service.

Let's now say your cluster main branch is `master` (the default value); your blog will also automatically be available
on `blog.mydomain.dom`.

**Note:** You can set your cluster domain to a completely different domain name to not "pollute" your production domain
and set to the services you want to run on the production domain name the `plimni.io/fqdn` annotation / tag with the
real, production ready domain name. If you do this, don't forget to make your service production domain name target
Plimni.


## Automatic certificate issuance and renewal (for HTTPS services)

If you set the `plimni.io/mode` flag to `https` for a service, Plimni will ask Certbot to automatically generate a
certificate for this service and will also automatically configure HAProxy to serve this certificate.

You have nothing else to do than set a flag.

Note that all your services share the same certificate (there isn't one certificate per service but one certificate for
the whole cluster).


## Automatic routing based on your services branches

Depending on the branches your services are (known with the `plimni.io/branch` flag), Plimni will automatically create
subdomains (one subdomain per branch) where your services can be reached. This allows you to deploy a testing branch
and have it accessible directly, on a different subdomain, so that other developers, the sales team or even directly
some selected customers can test your feature right away.


## Filtering of services responses

Sometimes you don't want to expose errors to the world. Let's say you have a service serving lots of real-time requests
and you don't want any error to be sent back to your API consumers. You can use the `plimni.io/http-sanitize-codes` and
`plimni.io/http-sanitize-return` flags to make HAProxy return the HTTP code you choose instead of a 503 or 404 error.


# How to run it?

Clone the repo, then depending on the orchestrator:


## Kubernetes

Check the `k8s/plimni.yml` file and change the resources allocated depending on your loadbalancer. Note that by default
Plimni will **only** run on a node with the `lb` **type** and a `lb=<something>:NoExecute` **taint** (to prevent normal
workload to be scheduled on the loadbalancer).

To add the `lb` type: `$ kubectl label nodes <loadbalancer-name> type=lb`.

To add the taint: `$ kubectl taint nodes <loadbalancer-name> lb=true:NoExecute` (this will evict all running pods from
your node).

Note that this will also create a `plimni` namespace.

Once you're good with the configuration, deploy it: `$ kubectl apply -f k8s/plimni.yml`


## Nomad

Check the `nomad/plimni.hcl` and `nomad/certbot.hcl` files and change the resources allocated depending on your
loadbalancer. Note that by default Plimni will **only** run on a node with the `lb` **type**.

To add the `lb` type to your loadbalancer, change its `nomad.hcl` configuration file and add:

```
client{
    ...

    meta {
        "type" = "lb"
    }
```

Then restart Nomad on this node.

Once you're good with the configuration deploy it: `$ nomad job run nomad/plimni.hcl && nomad job run nomad/certbot.hcl`


# How to configure it?

The options needed by Plimni are available with `plimni --help` (see the command help for extensive documentation):

| Option | Required? | Example | Description |
| --- | --- | --- | --- |
| `-o`<br/>`--orchestrator` | yes | "nomad" | Tells Plimni in which cluster it's running. |
| `-d`<br/>`--cluster-domain` | yes | "mydomain.com" | A domain which resolves to your loadbalancer Plimni is running on. |
| `-e`<br/>`--cluster-email` | no | "admin@domain.com" | The email used by Certbot to create an account at LetsEncrypt.<br/>Defaults to `postmaster@<cluster-domain>`. |
| `-b`<br/>`--cluster-branch` | no | The branch considered the default branch for short URLs.<br/>Default to `master`. |
| `--private-ip` | yes for Nomad | Nomad only. Put your loadbalancer private IP (or the IP Nomad binds services to). |
| `--init` | no | Whether to run Plimni in init mode (generate configurations and exit, don't try to reload HAProxy).<br/>Defaults to `false`. |
| `-t`<br/>`--sleep-time` | no | How long Plimni will wait between 2 runs, in seconds. The shorter, the more reactive it feels.<br/>Defaults to `5`. |
| `--haproxy-services-conf-file` | no | Where Plimni should write the HAProxy services configuration file. You should probably not change this.<br/>Defaults to `/usr/local/etc/haproxy/conf.d/services.cfg`. |
| `--haproxy-pid-file` | no | Where HAProxy should put its PID file. You should probably not change this.<br/>Defaults to `/usr/local/etc/haproxy/conf.d/haproxy.pid`. |
| `--haproxy-sanitize-conf-folder` | no | Where HAProxy should look for sanitized return files. You should probably not change this.<br/>Defaults to `/usr/local/etc/haproxy/sanitize.d`. |
| `--certbot-conf-folder` | no | Where the Certbot working directory should be. You should probably not change this.<br/>Defaults to `/usr/local/etc/haproxy/certs`. |

These options are configured in the `plimni ConfigMap` (for Kubernetes) and in the `env` block of the `plimni` task
(for Nomad).
They are only useful to make Plimni work, but this alone won't expose your services. You have to add **annotations**
(Kubernetes) or **tags** (Nomad) to them for Plimni to expose them.


# Service configuration

Plimni will automatically retrieve data from your **services** to know what to expose.
Depending on your orchestrator, you will need to set either annotations (Kubernetes) or tags (Nomad) to these services.

| Key | Value | Example | Description |
| --- | --- | --- | --- |
| `plimni.io/expose` | `true`/`false` | `"true"` | Whether or not to route traffic to the service.<br/>Useful to quickly unplug a service. |
| `plimni.io/branch` | `<str>` | `"feat/new-user"` | The branch the service is on. Used to generate the FQDN Plimni will use for this service. |
| `plimni.io/fqdn` | `<str>` | `blog.mysite.com"` | If you want to use a completely different FQDN than your `cluster_domain`, you can directly specify here the FQDN to answer to. |
| `plimni.io/mode` | `http`/`https` | `"https"` | HTTP for HTTP-only traffic, HTTPS for both HTTP and HTTPS.<br/>Defaults to `https`. |
| `plimni.io/http-port` | `<int>` | `"8080"` | The HTTP port to use.<br/>Defaults to `80`. |
| `plimni.io/https-port` | `<int>` | `"8443"` | The HTTPS port to use, if HTTPS mode.<br/>Defaults to `443`. |
| `plimni.io/http-sanitize-codes` | `<[]int>` | `"500,502,503,504"` | The codes (sent back by the service) you want to replace (= sanitize). |
| `plimni.io/http-sanitize-return` | `<int>` | `"202"` | The code you want to replace these sanitized values with. Mandatory if `http-sanitize-codes` is supplied. |


# Examples

In all these examples, your cluster domain is `example.com`.


## I want to expose my `blog` service to the Internet

Deploy your `blog` service on your cluster, then:


### Kubernetes

Deploy this:

```
apiVersion: v1
kind: Service
metadata:
  name: blog
  annotations:
    plimni.io/expose: "true"
spec:
  selector:
    app: blog
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 80
```


### Nomad

Edit your `blog.hcl` file and change the `service` block:

```
job "blog" {
    ...

    group "blog" {
        ...

        task "blog" {
            ...

            service {
                name = "blog"
                tags = [
                    "plimni.io/expose=true",
                ]
                port = "http"
            }
        }
    }
}
```

### URLs

You now can query any of these URLs:

- `http://blog.example.com` (short URL, considering the cluster main branch is `master`)
- `http://blog.master.example.com` (standard, branch-based URL)
- `https://blog.example.com`
- `https://blog.master.example.com`


## I want to expose a completely different URL than my "branch and cluster domain" opiniated URL for my store API


### Kubernetes

```
apiVersion: v1
kind: Service
metadata:
  name: store-api
  annotations:
    plimni.io/expose: "true"
    plimni.io/fqdn: "api.store.different-domain.com"
spec:
  selector:
    app: store-api
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 80
```


### Nomad

```
job "store" {
    ...

    group "store" {
        ...

        task "api" {
            ...

            service {
                name = "store-api"
                tags = [
                    "plimni.io/expose=true",
                    "plimni.io/fqdn=api.store.different-domain.com",
                ]
                port = "http"
            }
        }
    }
}
```


### URLs

You now can query any of these URLs:

- `http://api.store.different-domain.com`
- `https://api.store.different-domain.com`


## I want to catch all errors my API could return and return a 204 instead


### Kubernetes

```
apiVersion: v1
kind: Service
metadata:
  name: api
  annotations:
    plimni.io/expose: "true"
    plimni.io/http-sanitize-codes: "400,404,500,502,503,504"
    plimni.io/http-sanitize-return: "204"
spec:
  selector:
    app: api
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 80
```


### Nomad

```
job "api" {
    ...

    group "api" {
        ...

        task "api" {
            ...

            service {
                name = "api"
                tags = [
                    "plimni.io/expose=true",
                    "plimni.io/http-sanitize-codes=400,404,500,502,503,504"
                    "plimni.io/http-sanitize-return=204"
                ]
                port = "http"
            }
        }
    }
}
```


### URLs

You now can query any of these URLs:

- `http://api.example.com`
- `https://api.master.example.com`

A `204 No Content` will be returned instead of any error in the 400,404,500,502,503,504 range.
