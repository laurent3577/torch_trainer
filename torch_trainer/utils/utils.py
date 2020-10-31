import torch
from ..models import build_model


def load_from_path(path, return_config=False):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    data = torch.load(path, map_location=device)
    params = data["params"]
    config = data["cfg"]
    model = build_model(config)
    model.load_state_dict(params)
    print("Model loaded from: {}".format(path))
    if return_config:
        return model, config
    else:
        return model