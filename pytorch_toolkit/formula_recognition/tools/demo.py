"""
 Copyright (c) 2020 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import argparse
import os.path
import yaml

import cv2 as cv
from im2latex.data.utils import create_list_of_transforms
from im2latex.data.vocab import read_vocab
from im2latex.models.im2latex_model import Im2latexModel
from evaluation_tools import render_routine


class Im2latexDemo:
    def __init__(self, config):
        self.config = config
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(self.root_dir, config.get('model_path'))
        self.vocab = read_vocab(os.path.join(self.root_dir, config.get('vocab_path')))
        self.transform = create_list_of_transforms(config.get('transforms_list'))
        self.model = Im2latexModel(config.get('backbone_type', 'resnet'), config.get(
            'backbone_config'), len(self.vocab), config.get('head', {}))
        if self.model_path is not None:
            self.model.load_weights(self.model_path, map_location=config.get('map_location', 'cpu'))

        self.device = config.get('device', 'cpu')
        self.model = self.model.to(self.device)

    def __call__(self, img):
        img = self.transform(img)
        img = img[0].unsqueeze(0)
        img = img.to(self.device)
        _, targets = self.model(img)
        return self.vocab.construct_phrase(targets[0])


def parse_args():
    args = argparse.ArgumentParser()
    args.add_argument('--config')
    args.add_argument("-i", "--input", help="Path to a folder with images or path to an image files", required=True)
    return args.parse_args()


if __name__ == "__main__":
    args = parse_args()
    with open(args.config, 'r') as f:
        config = yaml.load(f, Loader=yaml.SafeLoader).get("demo")
    demo = Im2latexDemo(config)
    if os.path.isdir(args.input):
        inputs = sorted(os.path.join(args.input, inp)
                        for inp in os.listdir(args.input))
    else:
        inputs = [args.input]
    for inp in inputs:
        input_image = cv.imread(inp, cv.IMREAD_COLOR)
        assert input_image is not None, "Error reading image {}, please, check input path".format(inp)
        recognized_formula = demo(input_image)
        cv.imshow("Input image", input_image)
        print(recognized_formula)
        line_for_render = (recognized_formula, "output.png", "./")
        render_routine(line_for_render)
        rendered_formula = cv.imread("output.png", cv.IMREAD_UNCHANGED)
        cv.imshow("Predicted formula", rendered_formula)
        cv.waitKey(0)
        if os.path.exists("output.png"):
            os.remove("output.png")
