from tqdm import tqdm
import torch
import os

class Trainer():
    def __init__(self, model, train_loader, val_loader, optim, scheduler, loss_fn, hooks, config):
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.optim = optim
        self.scheduler = scheduler
        self.loss_fn = loss_fn
        self._register_hooks(hooks)
        self.step = 0
        self.config = config
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.save_path = os.path.join(config.OUTPUT_DIR, config.EXP_NAME + "_checkpoint.pth")

    def _register_hooks(self, hooks):
        self.hooks = hooks
        for hk in self.hooks:
            hk.trainer = self

    def _hook(self, method):
        out = False
        for hk in self.hooks:
            out = out or getattr(hk, method)()
        return out

    def _process_epoch(self):
        if self.in_train:
            self.model.train()
        else:
            self.model.eval()
        self.pbar = tqdm(self.train_loader)
        for img, target in self.pbar:
            self.step += 1
            self.input = img.to(self.device)
            self.target = target.to(self.device)
            self._hook('batch_begin')
            self._process_batch()
            self._hook('batch_end')

    def _process_batch(self):
        self.optim.zero_grad()
        self.output = self.model(self.input)
        self._hook('before_loss')
        self.loss = self.loss_fn(self.output, self.target)
        if self.in_train:
            self._hook('before_backward')
            self.loss.backward()
            self.optim.step()
            if self.scheduler.update_on_step:
                self.scheduler.step()

    def train(self, epoch):
        self.epoch = 1
        self._hook('train_begin')
        for i in range(epoch):
            self.in_train = True
            self._hook('epoch_begin')
            self._process_epoch()
            self._hook('epoch_end')
            if not self._hook('skip_val'):
                self.val()
            if not self.scheduler.update_on_step:
                self.scheduler.step()
            torch.save({
                'cfg':self.config,
                'params': self.model.state_dict()
                }, save_path)
            self.epoch += 1
        self.hook('train_end')

    def val(self):
        self.in_train = False
        self._hook('val_begin')
        self._process_epoch()
        self._hook('val_end')