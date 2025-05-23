# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
# Training the model

Basic run (on CPU for 50 epochs):
    python examples/asr/asr_transducer/speech_to_text_rnnt.py \
        # (Optional: --config-path=<path to dir of configs> --config-name=<name of config without .yaml>) \
        model.train_ds.manifest_filepath="<path to manifest file>" \
        model.validation_ds.manifest_filepath="<path to manifest file>" \
        trainer.devices=1 \
        trainer.accelerator='cpu' \
        trainer.max_epochs=50


Add PyTorch Lightning Trainer arguments from CLI:
    python speech_to_text_rnnt.py \
        ... \
        +trainer.fast_dev_run=true

Hydra logs will be found in "$(./outputs/$(date +"%y-%m-%d")/$(date +"%H-%M-%S")/.hydra)"
PTL logs will be found in "$(./outputs/$(date +"%y-%m-%d")/$(date +"%H-%M-%S")/lightning_logs)"

Override some args of optimizer:
    python speech_to_text_rnnt.py \
    --config-path="experimental/contextnet_rnnt" \
    --config-name="config_rnnt" \
    model.train_ds.manifest_filepath="./an4/train_manifest.json" \
    model.validation_ds.manifest_filepath="./an4/test_manifest.json" \
    trainer.devices=2 \
    trainer.precision=16 \
    trainer.max_epochs=2 \
    model.optim.betas=[0.8,0.5] \
    model.optim.weight_decay=0.0001

Override optimizer entirely
    python speech_to_text_rnnt.py \
    --config-path="experimental/contextnet_rnnt" \
    --config-name="config_rnnt" \
    model.train_ds.manifest_filepath="./an4/train_manifest.json" \
    model.validation_ds.manifest_filepath="./an4/test_manifest.json" \
    trainer.devices=2 \
    trainer.precision=16 \
    trainer.max_epochs=2 \
    model.optim.name=adamw \
    model.optim.lr=0.001 \
    ~model.optim.args \
    +model.optim.args.betas=[0.8,0.5]\
    +model.optim.args.weight_decay=0.0005

# Fine-tune a model

For documentation on fine-tuning this model, please visit -
https://docs.nvidia.com/deeplearning/nemo/user-guide/docs/en/main/asr/configs.html#fine-tuning-configurations

"""

import lightning.pytorch as pl
from omegaconf import OmegaConf

from nemo.collections.asr.models import EncDecRNNTModel
from nemo.core.config import hydra_runner
from nemo.utils import logging
from nemo.utils.exp_manager import exp_manager
from nemo.utils.trainer_utils import resolve_trainer_cfg


@hydra_runner(config_path="experimental/contextnet_rnnt", config_name="config_rnnt")
def main(cfg):
    logging.info(f'Hydra config: {OmegaConf.to_yaml(cfg)}')

    trainer = pl.Trainer(**resolve_trainer_cfg(cfg.trainer))
    exp_manager(trainer, cfg.get("exp_manager", None))
    asr_model = EncDecRNNTModel(cfg=cfg.model, trainer=trainer)

    # Initialize the weights of the model from another model, if provided via config
    asr_model.maybe_init_from_pretrained_checkpoint(cfg)

    trainer.fit(asr_model)

    if hasattr(cfg.model, 'test_ds') and cfg.model.test_ds.manifest_filepath is not None:
        if asr_model.prepare_test(trainer):
            trainer.test(asr_model)


if __name__ == '__main__':
    main()  # noqa pylint: disable=no-value-for-parameter
