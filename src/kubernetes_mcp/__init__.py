"""MCP tools for inspecting a Kubernetes cluster."""

from datetime import datetime, timezone
import os

from mcp.server.mcpserver import MCPServer
from kubernetes import client, config

mcp = MCPServer("kubernetes_mcp")

kubernetes_context = os.getenv("KUBERNETES_CONTEXT", "kind-dev101")
config.load_kube_config(context=kubernetes_context)

v1 = client.VersionApi()

@mcp.tool()
def get_k8s_version():
    """Return the Kubernetes cluster version."""
    version_info = v1.get_code()
    return version_info.git_version

@mcp.tool()
def get_deployments(namespace: str) -> list[str]:
    """Return deployment names in a Kubernetes namespace."""
    apps_v1 = client.AppsV1Api()
    deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
    return [deployment.metadata.name for deployment in deployments.items]

@mcp.tool()
def scale_deployment(namespace: str, deployment: str, replicas: int) -> str:
    """Set a deployment's desired number of pod replicas.

    Args:
        namespace: Kubernetes namespace containing the deployment.
        deployment: Name of the deployment to scale.
        replicas: Desired pod count. Must be zero or greater.

    Returns:
        A confirmation message after the scale request is accepted.

    Raises:
        ValueError: If replicas is negative.
    """
    if replicas < 0:
        raise ValueError("replicas must be non-negative")

    apps_v1 = client.AppsV1Api()
    apps_v1.patch_namespaced_deployment_scale(
        name=deployment,
        namespace=namespace,
        body={"spec": {"replicas": replicas}},
    )
    return f"Scaled deployment {deployment} to {replicas} replicas"

@mcp.tool()
def restart_deployment(namespace: str, deployment: str) -> str:
    """Roll out a restart of all pods managed by a deployment.

    The restart is triggered by updating the pod template's restart timestamp
    annotation, which causes Kubernetes to create a new deployment revision.

    Args:
        namespace: Kubernetes namespace containing the deployment.
        deployment: Name of the deployment whose pods should be restarted.

    Returns:
        A confirmation message after the restart request is accepted.
    """
    apps_v1 = client.AppsV1Api()
    restarted_at = datetime.now(timezone.utc).isoformat()
    apps_v1.patch_namespaced_deployment(
        name=deployment,
        namespace=namespace,
        body={
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": restarted_at,
                        }
                    }
                }
            }
        },
    )
    return f"Restarted deployment {deployment}"

@mcp.tool()
def get_pods(namespace: str, deployment: str) -> list[dict[str, str | int | None]]:
    """Return pod names, restart counts, and creation times for a deployment."""
    apps_v1 = client.AppsV1Api()
    deployment_info = apps_v1.read_namespaced_deployment(
        name=deployment,
        namespace=namespace,
    )
    selector = ",".join(
        f"{key}={value}"
        for key, value in deployment_info.spec.selector.match_labels.items()
    )

    core_v1 = client.CoreV1Api()
    pods = core_v1.list_namespaced_pod(
        namespace=namespace,
        label_selector=selector,
    )
    return [
        {
            "name": pod.metadata.name,
            "restart_count": sum(
                container_status.restart_count
                for container_status in (pod.status.container_statuses or [])
            ),
            "creation_time": (
                pod.metadata.creation_timestamp.isoformat()
                if pod.metadata.creation_timestamp
                else None
            ),
        }
        for pod in pods.items
    ]

@mcp.tool()
def get_logs(namespace: str, pod_name: str, lines: int = 100) -> str:
    """Return the requested number of recent log lines for a pod."""
    core_v1 = client.CoreV1Api()
    return core_v1.read_namespaced_pod_log(
        name=pod_name,
        namespace=namespace,
        tail_lines=lines,
    )

if __name__ == "__main__":
    mcp.run()