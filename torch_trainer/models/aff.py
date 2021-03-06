import torch.nn as nn
import torch


def conv1x1block(in_channels, out_channels, use_bn, use_act):
    modules = [
        nn.Conv2d(
            in_channels, out_channels, kernel_size=1, stride=1, padding=0, bias=False
        )
    ]
    if use_bn:
        modules.append(nn.BatchNorm2d(num_features=out_channels))
    if use_act:
        modules.append(nn.LeakyReLU(inplace=True))
    return nn.Sequential(*modules)


class MSCam(nn.Module):
    def __init__(self, in_channels, ratio):
        super(MSCam, self).__init__()
        proj_dim = in_channels // ratio
        self._global = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            conv1x1block(in_channels, proj_dim, True, True),
            conv1x1block(proj_dim, in_channels, True, False),
        )
        self._local = nn.Sequential(
            conv1x1block(in_channels, proj_dim, True, True),
            conv1x1block(proj_dim, in_channels, True, False),
        )

    def forward(self, x):
        out = torch.sigmoid(self._local(x) + self._global(x))
        return out


class AFF(nn.Module):
    def __init__(self, in_channels, ratio=16):
        super(AFF, self).__init__()
        self.mscam = MSCam(in_channels, ratio)
        self.bn = nn.BatchNorm2d(num_features=in_channels)
        self.act = nn.LeakyReLU()

    def forward(self, identity, resid):
        att = self.mscam(identity + resid)
        out = 2 * att * resid + 2 * (1 - att) * identity
        out = self.bn(out)
        out = self.act(out)
        return out
