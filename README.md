# Kubernetes MCP

An MCP server that exposes common Kubernetes inspection and deployment operations to an MCP client.

The project is designed for local Kind clusters. It connects to the kubeconfig context in the
`KUBERNETES_CONTEXT` environment variable, defaulting to `kind-dev101`.

## Features

The server provides these MCP tools:

| Tool | Description |
| --- | --- |
| `get_k8s_version` | Returns the Kubernetes cluster version. |
| `get_deployments` | Lists deployments in a namespace. |
| `get_pods` | Lists pods for a deployment, including restart counts and creation times. |
| `get_logs` | Returns recent logs for a pod. |
| `scale_deployment` | Changes the desired replica count for a deployment. |
| `restart_deployment` | Triggers a rolling restart by updating the deployment pod template. |

## Prerequisites

- Python 3.13 or later
- [uv](https://docs.astral.sh/uv/)
- [Docker](https://docs.docker.com/get-docker/)
- [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/)
- `kubectl`

## Create the Kind clusters

Create the local clusters from PowerShell or a terminal:

```bash
kind create cluster --name dev101
kind create cluster --name sit101
kind create cluster --name prod101
```

Kind creates these kubeconfig contexts:

```text
kind-dev101
kind-sit101
kind-prod101
```

Verify the contexts:

```bash
kubectl config get-contexts
```

## Install dependencies

From the repository root:

```bash
uv sync
```

## Run the MCP server

Start the server over the standard MCP stdio transport:

```bash
uv run python src/kubernetes_mcp/__init__.py
```

The server reads the Kubernetes configuration from the default kubeconfig location. Set
`KUBERNETES_CONTEXT` before launching it to choose a cluster:

PowerShell:

```powershell
$env:KUBERNETES_CONTEXT = "kind-sit101"
uv run python src/kubernetes_mcp/__init__.py
```

For production, use `kind-prod101`. If the variable is omitted, the server connects to
`kind-dev101`.

## Configure an MCP client

Add the server to an MCP client that supports stdio servers. The command should point to this
repository and use the same launcher shown above:

```json
{
	"mcpServers": {
		"kubernetes": {
			"command": "uv",
			"env": {
				"KUBERNETES_CONTEXT": "kind-sit101"
			},
			"args": [
				"run",
				"--directory",
				"C:\\Users\\<your-user>\\kubernetes-mcp",
				"python",
				"src/kubernetes_mcp/__init__.py"
			]
		}
	}
}
```

Replace the repository path with the path on your machine. Keep the MCP server process attached to
the client; it communicates through stdin and stdout.

## Deploy the sample workload

The repository includes an NGINX deployment and service in `k8s/deployment.yaml`:

```bash
kubectl config use-context kind-dev101
kubectl apply -f k8s/deployment.yaml
kubectl get deployments,pods,services -n default
```

The sample deployment is named `nginx` and runs two replicas.

## Example tool calls

Use the MCP client to call tools with arguments such as:

```json
{
	"namespace": "default",
	"deployment": "nginx",
	"replicas": 3
}
```

This payload can be used with `scale_deployment` to scale NGINX to three replicas. To restart the
deployment, call `restart_deployment` with:

```json
{
	"namespace": "default",
	"deployment": "nginx"
}
```

## Switching clusters

Set `KUBERNETES_CONTEXT` in the MCP client configuration and restart the server process. For
example, use `kind-dev101`, `kind-sit101`, or `kind-prod101`. The MCP server uses the selected
context directly, regardless of which context is active in `kubectl`.

## Stop and delete clusters

To stop using the local clusters and remove their containers:

```bash
kind delete cluster --name dev101
kind delete cluster --name sit101
kind delete cluster --name prod101
```

Deleting a Kind cluster removes its local Kubernetes resources. Do not run these commands for a
cluster containing data you need to keep.
