import torch, time
torch.backends.cuda.enable_flash_sdp(False)
torch.backends.cuda.enable_mem_efficient_sdp(False)
torch.backends.cuda.enable_math_sdp(True)
if torch.cuda.is_available():
    _d = torch.device("cuda:0")
    for _ in range(10):
        _x = torch.randn(256, 256, device=_d)
        _y = torch.mm(_x, _x)
    torch.cuda.synchronize()
    del _x, _y
    torch.cuda.empty_cache()
    time.sleep(2)

import torch
import json
import torch.backends.cudnn as cudnn

from config import args
from trainer import Trainer
from logger_config import logger


def main():
    # Thorough CUDA warmup — must happen before model creation on WSL2/Blackwell
    import torch, time
    if torch.cuda.is_available():
        dev = torch.device('cuda:0')
        # multiple ops to fully initialize the driver
        for _ in range(5):
            x = torch.randn(512, 512, device=dev)
            y = torch.mm(x, x)
        torch.cuda.synchronize()
        del x, y
        torch.cuda.empty_cache()
        time.sleep(1)  # give WSL2 driver a moment
    ngpus_per_node = torch.cuda.device_count()
    cudnn.benchmark = True

    logger.info("Use {} gpus for training".format(ngpus_per_node))

    trainer = Trainer(args, ngpus_per_node=ngpus_per_node)
    logger.info('Args={}'.format(json.dumps(args.__dict__, ensure_ascii=False, indent=4)))
    trainer.train_loop()


if __name__ == '__main__':
    main()
