import dgl
import torch


def main() -> None:
    print(f"torch={torch.__version__}")
    print(f"torch_cuda={torch.version.cuda}")
    print(f"torch_cuda_available={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"torch_device={torch.cuda.get_device_name(0)}")
        print(f"torch_capability={torch.cuda.get_device_capability(0)}")
        x = torch.randn(4, 4, device="cuda")
        print(f"torch_cuda_tensor_mean={float(x.mean())}")

    print(f"dgl={dgl.__version__}")
    graph = dgl.graph(([0, 1], [1, 2]), num_nodes=3)
    cuda_graph = graph.to("cuda")
    print(f"dgl_cuda_graph={cuda_graph}")


if __name__ == "__main__":
    main()
